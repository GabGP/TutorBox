#include "ClickerApp.h"

#include <stdarg.h>
#include <stdio.h>
#include <string.h>

namespace {

// true once `now` has reached `deadline`, also across the 49-day millis() wrap.
bool reached(uint32_t nowMs, uint32_t deadlineMs) {
  return static_cast<int32_t>(nowMs - deadlineMs) >= 0;
}

void copyText(char* out, size_t cap, const char* text) {
  strncpy(out, text, cap - 1);
  out[cap - 1] = '\0';
}

}  // namespace

ClickerApp::ClickerApp()
    : deviceId_(""),
      firmware_(""),
      log_(nullptr),
      phase_(Phase::LookingForWifi),
      wifi_(false),
      inFlight_(false),
      failures_(0),
      rssi_(0),
      batteryPct_(-1),
      loginRefused_(false),
      nextAuthAt_(0),
      nextPollAt_(0),
      nextBeatAt_(0),
      roundOpen_(false),
      roundSeen_(false),
      roundSeenAt_(0),
      votePending_(false),
      voteOption_(0),
      voteResponseMs_(0),
      voteAttempts_(0),
      voteNextAt_(0) {
  secret_[0] = '\0';
  token_[0] = '\0';
  sessionId_[0] = '\0';
  roundId_[0] = '\0';
  answeredRound_[0] = '\0';
  voteSession_[0] = '\0';
  voteRound_[0] = '\0';
}

void ClickerApp::begin(const char* deviceId, const char* firmware, const char* secret,
                       LogFn log, uint32_t nowMs) {
  deviceId_ = deviceId;
  firmware_ = firmware;
  log_ = log;
  if (protocol::isSecret(secret)) copyText(secret_, sizeof(secret_), secret);
  nextAuthAt_ = nowMs;
  logf("Clicker %s, firmware %s: looking for Wi-Fi", deviceId_, firmware_);
}

// ----------------------------------------------------------------------------
// Inputs
// ----------------------------------------------------------------------------

void ClickerApp::setWifi(bool connected, uint32_t nowMs) {
  if (connected == wifi_) return;
  wifi_ = connected;
  if (!connected) {
    logf("Wi-Fi lost, reconnecting");
    enter(Phase::LookingForWifi);
    inFlight_ = false;
    roundOpen_ = false;
    if (votePending_) {
      cancelVote(StatusLed::Red, nowMs);
      logf("Vote %c was NOT sent (no Wi-Fi). Press again when the light is white.",
           voteOption_);
    }
    return;
  }
  failures_ = 0;
  if (token_[0] != '\0') {
    // The token outlives a Wi-Fi drop. If the TutorBox ended it meanwhile, the
    // heartbeat sent right now gets a 401 and the clicker logs in again.
    logf("Wi-Fi connected again");
    enter(Phase::Ready);
    nextBeatAt_ = nowMs;
    nextPollAt_ = nowMs;
    return;
  }
  logf("Wi-Fi connected");
  startLogin(nowMs);
}

void ClickerApp::setVitals(int rssi, int batteryPct) {
  rssi_ = rssi;
  batteryPct_ = batteryPct;
}

void ClickerApp::setSecret(const char* secret, uint32_t nowMs) {
  if (!protocol::isSecret(secret)) return;
  copyText(secret_, sizeof(secret_), secret);
  dropToken();
  loginRefused_ = false;
  failures_ = 0;
  if (votePending_) cancelVote(StatusLed::Red, nowMs);
  logf("New secret stored");
  if (wifi_) startLogin(nowMs);
}

void ClickerApp::onButton(char option, uint32_t nowMs) {
  if (votePending_) return;  // one vote in flight at a time
  if (phase_ != Phase::Ready) {
    const bool teacher = phase_ == Phase::Unassigned || phase_ == Phase::Rejected ||
                         phase_ == Phase::NeedsSecret;
    led_.blink(teacher ? StatusLed::Magenta : StatusLed::Red, 3, nowMs);
    logf("Button %c ignored: %s", option,
         teacher ? "this clicker needs the teacher (see README)" : "not connected yet");
    return;
  }
  if (!armed()) {
    led_.blink(StatusLed::Red, 3, nowMs);
    logf("Button %c ignored: %s", option,
         roundOpen_ ? "this question is already answered" : "no question is open");
    return;
  }
  votePending_ = true;
  voteOption_ = option;
  copyText(voteSession_, sizeof(voteSession_), sessionId_);
  copyText(voteRound_, sizeof(voteRound_), roundId_);
  voteResponseMs_ = nowMs - roundSeenAt_;
  voteAttempts_ = 0;
  voteNextAt_ = nowMs;
  logf("Button %c: sending vote for %s", option, voteRound_);
}

void ClickerApp::onResponse(RequestKind kind, int status, const char* body,
                            uint32_t nowMs) {
  inFlight_ = false;
  if (kind == RequestKind::Auth) onAuth(status, body, nowMs);
  if (kind == RequestKind::Poll) onPoll(status, body, nowMs);
  if (kind == RequestKind::Heartbeat) onHeartbeat(status, body, nowMs);
  if (kind == RequestKind::Vote) onVote(status, body, nowMs);
}

// ----------------------------------------------------------------------------
// Outputs
// ----------------------------------------------------------------------------

bool ClickerApp::nextRequest(uint32_t nowMs, Request& out) {
  if (!wifi_ || inFlight_) return false;
  out.kind = RequestKind::None;
  out.post = true;
  out.bearer = nullptr;
  out.body[0] = '\0';

  if (token_[0] == '\0') {
    // No token: the only thing to do is log in, when that can still work.
    if (secret_[0] == '\0' || loginRefused_ || !reached(nowMs, nextAuthAt_)) {
      return false;
    }
    out.kind = RequestKind::Auth;
    copyText(out.path, sizeof(out.path), protocol::kAuthPath);
    protocol::authBody(out.body, sizeof(out.body), deviceId_, secret_);
    nextAuthAt_ = nowMs + kRetryEveryMs;  // replaced when the reply arrives
  } else if (votePending_) {
    if (!reached(nowMs, voteNextAt_)) return false;  // between two tries of a vote
    out.kind = RequestKind::Vote;
    out.bearer = token_;
    protocol::votePath(out.path, sizeof(out.path), voteSession_);
    protocol::voteBody(out.body, sizeof(out.body), voteOption_, voteResponseMs_);
    voteAttempts_++;
  } else if (reached(nowMs, nextBeatAt_)) {
    out.kind = RequestKind::Heartbeat;
    out.bearer = token_;
    copyText(out.path, sizeof(out.path), protocol::kHeartbeatPath);
    protocol::heartbeatBody(out.body, sizeof(out.body), rssi_, batteryPct_);
    nextBeatAt_ = nowMs + kHeartbeatEveryMs;
  } else if (reached(nowMs, nextPollAt_)) {
    out.kind = RequestKind::Poll;
    out.post = false;  // public: the token is not sent where it is not needed
    copyText(out.path, sizeof(out.path), protocol::kSessionPath);
    nextPollAt_ = nowMs + kPollEveryMs;  // replaced when the reply arrives
  } else {
    return false;
  }
  inFlight_ = true;
  return true;
}

StatusLed::Color ClickerApp::ledColor(uint32_t nowMs) {
  switch (phase_) {
    case Phase::LookingForWifi:
      led_.setPattern(StatusLed::Blue, 150, 150, nowMs);
      break;
    case Phase::Connecting:
      led_.setPattern(StatusLed::Blue, 1, 0, nowMs);
      break;
    case Phase::ServerUnreachable:
      led_.setPattern(StatusLed::Blue, 1000, 1000, nowMs);
      break;
    case Phase::NeedsSecret:
    case Phase::Rejected:
      led_.setPattern(StatusLed::Magenta, 150, 150, nowMs);
      break;
    case Phase::Unassigned:
      led_.setPattern(StatusLed::Magenta, 1000, 1000, nowMs);
      break;
    case Phase::Ready:
      if (votePending_) {
        led_.setPattern(StatusLed::Yellow, 1, 0, nowMs);
      } else if (armed()) {
        led_.setPattern(StatusLed::White, 700, 300, nowMs);
      } else {
        led_.setPattern(StatusLed::Green, 60, 2940, nowMs);  // "I'm on" blip
      }
      break;
  }
  return led_.colorAt(nowMs);
}

bool ClickerApp::statusLedOn(uint32_t nowMs) const {
  return wifi_ || (nowMs / 150) % 2 == 0;
}

bool ClickerApp::armed() const {
  return phase_ == Phase::Ready && !votePending_ && roundOpen_ &&
         roundId_[0] != '\0' && strcmp(roundId_, answeredRound_) != 0;
}

const char* ClickerApp::phaseName() const {
  switch (phase_) {
    case Phase::LookingForWifi:
      return "looking-for-wifi";
    case Phase::Connecting:
      return "connecting";
    case Phase::ServerUnreachable:
      return "server-unreachable";
    case Phase::NeedsSecret:
      return "needs-secret";
    case Phase::Rejected:
      return "rejected";
    case Phase::Unassigned:
      return "unassigned";
    case Phase::Ready:
      return "ready";
  }
  return "?";
}

// ----------------------------------------------------------------------------
// Server replies
// ----------------------------------------------------------------------------

void ClickerApp::onAuth(int status, const char* body, uint32_t nowMs) {
  char username[protocol::kUsernameSize] = "";
  if (status == 200 &&
      protocol::parseAuth(body, token_, sizeof(token_), username, sizeof(username))) {
    failures_ = 0;
    logf("Assigned to %s: ready to vote", username[0] != '\0' ? username : "a student");
    enter(Phase::Ready);
    nextBeatAt_ = nowMs;  // show up in the teacher's lobby at once
    nextPollAt_ = nowMs;
    return;
  }

  // Every other answer means no token. A vote that was waiting for one is dropped
  // and shown, never sent late.
  const bool teacher = status == 401 || status == 403 || status == 422 || status == 429;
  if (votePending_) {
    cancelVote(teacher ? StatusLed::Magenta : StatusLed::Red, nowMs);
    logf("Vote %c was NOT sent (no session)", voteOption_);
  }
  char detail[96] = "";
  protocol::parseDetail(body, detail, sizeof(detail));

  if (status == 403) {
    if (phase_ != Phase::Unassigned) {
      logf("Connected. Waiting for the teacher to assign %s to a student", deviceId_);
    }
    enter(Phase::Unassigned);
    failures_ = 0;
    nextAuthAt_ = nowMs + kUnassignedEveryMs;
    return;
  }
  if (status == 401 || status == 422) {
    // A refused secret counts against this clicker on the TutorBox, and enough of
    // them lock it out for up to 16 minutes: do not ask again with the same secret.
    loginRefused_ = true;
    enter(Phase::Rejected);
    failures_ = 0;
    logf("TutorBox refused this clicker's secret (HTTP %d %s)", status, detail);
    logf("Fix: set %s up again over USB (README: USB setup)", deviceId_);
    return;
  }
  if (status == 429) {
    enter(Phase::Rejected);
    failures_ = 0;
    nextAuthAt_ = nowMs + kLockedOutEveryMs;
    logf("TutorBox locked this clicker out after refused logins: asking again in 30 s");
    return;
  }

  nextAuthAt_ = nowMs + kRetryEveryMs;
  if (status == 404) {
    logf("TutorBox has no clicker login (HTTP 404): update the backend");
  } else if (status == 200) {
    logf("Login reply was not understood");
  } else {
    logf("Login failed (%d %s)", status, detail);
  }
  countFailure();
}

void ClickerApp::onPoll(int status, const char* body, uint32_t nowMs) {
  protocol::SessionView view;
  const bool running = status == 200 && protocol::parseSession(body, view);
  if (running || status == 404) {  // 404: no match is running, which is normal
    failures_ = 0;
    nextPollAt_ = nowMs + kPollEveryMs;
    if (phase_ != Phase::Ready) logf("TutorBox answers again");
    enter(Phase::Ready);
    if (running) {
      updateRound(view, nowMs);
    } else {
      roundOpen_ = false;
    }
    return;
  }
  nextPollAt_ = nowMs + kRetryEveryMs;
  if (status == 200) {
    logf("Session reply was not understood");
  } else {
    logf("TutorBox did not answer (%d)", status);
  }
  countFailure();
}

void ClickerApp::onHeartbeat(int status, const char* body, uint32_t nowMs) {
  if (status == 401) {
    // Unassigned, reassigned, deleted, a new secret, or 12 hours passed.
    logf("TutorBox ended this clicker's session: logging in again");
    dropToken();
    startLogin(nowMs);
    return;
  }
  if (status >= 400 && status < 500) {
    char detail[96] = "";
    protocol::parseDetail(body, detail, sizeof(detail));
    logf("Heartbeat refused (HTTP %d %s)", status, detail);
  }
  // No answer at all: the poll, sent five times as often, reports that.
}

void ClickerApp::updateRound(const protocol::SessionView& view, uint32_t nowMs) {
  copyText(sessionId_, sizeof(sessionId_), view.sessionId);
  if (strcmp(view.roundId, roundId_) != 0) {
    copyText(roundId_, sizeof(roundId_), view.roundId);
    roundSeen_ = false;
  }
  roundOpen_ = view.roundOpen;
  if (armed() && !roundSeen_) {
    roundSeen_ = true;
    roundSeenAt_ = nowMs;
    logf("Question open (%s): press A, B, C or D", roundId_);
  }
}

void ClickerApp::onVote(int status, const char* body, uint32_t nowMs) {
  char detail[96] = "";
  protocol::parseDetail(body, detail, sizeof(detail));
  if (status == 200) {
    finishVote(true, nowMs);
    logf("Vote %c counted", voteOption_);
    return;
  }
  if (status == 409 || status == 404) {
    // "Already voted" on a retry means the first try did arrive. Any other refusal
    // (the round closed, the match ended) is not a confirmation.
    const bool counted =
        status == 409 && voteAttempts_ > 1 && protocol::isAlreadyVoted(detail);
    finishVote(counted, nowMs);
    if (counted) {
      logf("Vote %c counted (confirmed on retry)", voteOption_);
    } else {
      logf("Vote %c not accepted (%s)", voteOption_, detail);
    }
    return;
  }
  if (status == 401) {
    // The session ended under us. The vote stays pending: log in, then send it.
    if (voteAttempts_ >= kVoteAttempts) cancelVote(StatusLed::Red, nowMs);
    logf("Vote %c: the session ended, logging in again", voteOption_);
    dropToken();
    startLogin(nowMs);
    return;
  }
  if ((status < 0 || status >= 500) && voteAttempts_ < kVoteAttempts) {
    voteNextAt_ = nowMs + kVoteRetryMs;  // network hiccup: same vote again
    logf("Vote %c: no answer (%d), retrying", voteOption_, status);
    return;
  }
  cancelVote(StatusLed::Red, nowMs);
  logf("Vote %c failed (HTTP %d %s). Press again while the light is white.",
       voteOption_, status, detail);
}

void ClickerApp::startLogin(uint32_t nowMs) {
  if (secret_[0] == '\0') {
    enter(Phase::NeedsSecret);
    logf("No secret yet: set %s up over USB (README: USB setup)", deviceId_);
    return;
  }
  if (loginRefused_) {
    enter(Phase::Rejected);
    return;
  }
  logf("Logging in to the TutorBox");
  enter(Phase::Connecting);
  nextAuthAt_ = nowMs;
}

void ClickerApp::dropToken() {
  memset(token_, 0, sizeof(token_));
  roundOpen_ = false;
}

void ClickerApp::countFailure() {
  if (failures_ < 255) failures_++;
  if (failures_ >= kFailuresBeforeUnreachable) enter(Phase::ServerUnreachable);
}

void ClickerApp::cancelVote(StatusLed::Color color, uint32_t nowMs) {
  votePending_ = false;
  led_.blink(color, 3, nowMs);
}

void ClickerApp::finishVote(bool counted, uint32_t nowMs) {
  votePending_ = false;
  copyText(answeredRound_, sizeof(answeredRound_), voteRound_);  // done either way
  if (counted) {
    led_.flash(StatusLed::Green, 1500, nowMs);
  } else {
    led_.blink(StatusLed::Red, 3, nowMs);
  }
  nextPollAt_ = nowMs + 300;  // refresh the round state soon
}

void ClickerApp::enter(Phase phase) { phase_ = phase; }

void ClickerApp::logf(const char* format, ...) {
  if (log_ == nullptr) return;
  char line[160];
  va_list args;
  va_start(args, format);
  vsnprintf(line, sizeof(line), format, args);
  va_end(args);
  log_(line);
}
