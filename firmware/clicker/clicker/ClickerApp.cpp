#include "ClickerApp.h"

#include <stdarg.h>
#include <stdio.h>
#include <string.h>

namespace {

// true once `now` has reached `deadline`, also across the 49-day millis() wrap.
bool reached(uint32_t nowMs, uint32_t deadlineMs) {
  return static_cast<int32_t>(nowMs - deadlineMs) >= 0;
}

void copyId(char* out, const char* id) {
  strncpy(out, id, protocol::kRoundIdSize - 1);
  out[protocol::kRoundIdSize - 1] = '\0';
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
      nextCheckinAt_(0),
      rssi_(0),
      batteryMv_(-1),
      roundOpen_(false),
      votedOnServer_(false),
      roundSeen_(false),
      roundSeenAt_(0),
      votePending_(false),
      voteOption_(0),
      voteResponseMs_(0),
      voteAttempts_(0),
      voteNextAt_(0) {
  roundId_[0] = '\0';
  answeredRound_[0] = '\0';
  voteRound_[0] = '\0';
}

void ClickerApp::begin(const char* deviceId, const char* firmware, LogFn log,
                       uint32_t nowMs) {
  deviceId_ = deviceId;
  firmware_ = firmware;
  log_ = log;
  nextCheckinAt_ = nowMs;
  logf("Clicker %s, firmware %s: looking for Wi-Fi", deviceId_, firmware_);
}

// ----------------------------------------------------------------------------
// Inputs
// ----------------------------------------------------------------------------

void ClickerApp::setWifi(bool connected, uint32_t nowMs) {
  if (connected == wifi_) return;
  wifi_ = connected;
  if (connected) {
    logf("Wi-Fi connected, checking in with the TutorBox");
    failures_ = 0;
    nextCheckinAt_ = nowMs;
    enter(Phase::Connecting);
    return;
  }
  logf("Wi-Fi lost, reconnecting");
  enter(Phase::LookingForWifi);
  inFlight_ = false;
  if (votePending_) {
    votePending_ = false;
    led_.blink(StatusLed::Red, 3, nowMs);
    logf("Vote %c was NOT sent (no Wi-Fi). Press again when the light is white.",
         voteOption_);
  }
}

void ClickerApp::setVitals(int rssi, int batteryMv) {
  rssi_ = rssi;
  batteryMv_ = batteryMv;
}

void ClickerApp::onButton(char option, uint32_t nowMs) {
  if (votePending_) return;  // one vote in flight at a time
  if (phase_ != Phase::Ready) {
    const bool teacher = phase_ == Phase::Unassigned || phase_ == Phase::Rejected;
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
  copyId(voteRound_, roundId_);
  voteResponseMs_ = nowMs - roundSeenAt_;
  voteAttempts_ = 0;
  voteNextAt_ = nowMs;
  logf("Button %c: sending vote for %s", option, voteRound_);
}

void ClickerApp::onResponse(RequestKind kind, int status, const char* body,
                            uint32_t nowMs) {
  inFlight_ = false;
  if (kind == RequestKind::Checkin) onCheckin(status, body, nowMs);
  if (kind == RequestKind::Vote) onVote(status, body, nowMs);
}

// ----------------------------------------------------------------------------
// Outputs
// ----------------------------------------------------------------------------

bool ClickerApp::nextRequest(uint32_t nowMs, Request& out) {
  if (!wifi_ || inFlight_) return false;
  if (votePending_ && reached(nowMs, voteNextAt_)) {
    inFlight_ = true;
    out.kind = RequestKind::Vote;
    out.path = protocol::kVotePath;
    protocol::voteBody(out.body, sizeof(out.body), voteRound_, voteOption_,
                       voteResponseMs_);
    voteAttempts_++;
    return true;
  }
  if (!votePending_ && reached(nowMs, nextCheckinAt_)) {
    inFlight_ = true;
    out.kind = RequestKind::Checkin;
    out.path = protocol::kCheckinPath;
    protocol::checkinBody(out.body, sizeof(out.body), firmware_, rssi_, batteryMv_);
    nextCheckinAt_ = nowMs + kCheckinEveryMs;  // replaced when the reply arrives
    return true;
  }
  return false;
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
  return phase_ == Phase::Ready && !votePending_ && roundOpen_ && !votedOnServer_ &&
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

void ClickerApp::onCheckin(int status, const char* body, uint32_t nowMs) {
  protocol::CheckinReply reply;
  if (status == 200 && protocol::parseCheckin(body, reply)) {
    failures_ = 0;
    nextCheckinAt_ = nowMs + kCheckinEveryMs;
    if (!reply.assigned) {
      if (phase_ != Phase::Unassigned) {
        logf("Connected. Waiting for the teacher to assign %s to a student", deviceId_);
      }
      enter(Phase::Unassigned);
      roundOpen_ = false;
      return;
    }
    if (phase_ != Phase::Ready) logf("Assigned to a student: ready to vote");
    enter(Phase::Ready);
    updateRound(reply, nowMs);
    return;
  }

  char detail[96] = "";
  protocol::parseDetail(body, detail, sizeof(detail));
  if (status == 401 || status == 403 || status == 422) {
    if (phase_ != Phase::Rejected) {
      logf("TutorBox refused this clicker (HTTP %d: %s)", status, detail);
      logf("Fix: the teacher removes %s from the clicker list, it then re-enrolls",
           deviceId_);
    }
    enter(Phase::Rejected);
    failures_ = 0;
    nextCheckinAt_ = nowMs + kRejectedEveryMs;
    return;
  }

  failures_++;
  nextCheckinAt_ = nowMs + kRetryEveryMs;
  if (status == 404) {
    logf("TutorBox has no clicker API (HTTP 404): update the backend");
  } else if (status == 200) {
    logf("Check-in reply was not understood");
  } else {
    logf("Check-in failed (%d %s)", status, detail);
  }
  if (failures_ >= kFailuresBeforeUnreachable) enter(Phase::ServerUnreachable);
}

void ClickerApp::updateRound(const protocol::CheckinReply& reply, uint32_t nowMs) {
  if (strcmp(reply.roundId, roundId_) != 0) {
    copyId(roundId_, reply.roundId);
    roundSeen_ = false;
  }
  roundOpen_ = reply.roundOpen;
  votedOnServer_ = reply.voted;
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
  if (status == 409) {
    // A retry that meets "already voted" means the first try did arrive.
    const bool counted = voteAttempts_ > 1;
    finishVote(counted, nowMs);
    if (counted) {
      logf("Vote %c counted (confirmed on retry)", voteOption_);
    } else {
      logf("Vote %c not accepted (%s)", voteOption_, detail);
    }
    return;
  }
  if (status == 401 || status == 403) {
    votePending_ = false;
    enter(status == 401 ? Phase::Rejected : Phase::Unassigned);
    led_.blink(StatusLed::Magenta, 3, nowMs);
    logf("Vote refused (HTTP %d: %s): this clicker needs the teacher", status, detail);
    nextCheckinAt_ = nowMs;
    return;
  }
  if ((status < 0 || status >= 500) && voteAttempts_ < kVoteAttempts) {
    voteNextAt_ = nowMs + kVoteRetryMs;  // network hiccup: same vote again
    logf("Vote %c: no answer (%d), retrying", voteOption_, status);
    return;
  }
  votePending_ = false;
  led_.blink(StatusLed::Red, 3, nowMs);
  logf("Vote %c failed (HTTP %d %s). Press again while the light is white.",
       voteOption_, status, detail);
}

void ClickerApp::finishVote(bool counted, uint32_t nowMs) {
  votePending_ = false;
  copyId(answeredRound_, voteRound_);  // either way this round is done for us
  if (counted) {
    led_.flash(StatusLed::Green, 1500, nowMs);
  } else {
    led_.blink(StatusLed::Red, 3, nowMs);
  }
  nextCheckinAt_ = nowMs + 300;  // refresh the round state soon
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
