// The clicker's brain: what to send to the TutorBox, and what the LED should show.
//
// It never touches pins, Wi-Fi or HTTP itself. clicker.ino feeds it what happened
// (Wi-Fi up? which button? what did the server answer?) and does what it asks.
// That split lets hosttest/ run this exact code on a PC against a real backend.
#pragma once

#include <stddef.h>
#include <stdint.h>

#include "Protocol.h"
#include "StatusLed.h"

class ClickerApp {
 public:
  enum class Phase : uint8_t {
    LookingForWifi,     // blue, fast blink
    Connecting,         // blue, steady: Wi-Fi up, logging in to the TutorBox
    ServerUnreachable,  // blue, slow blink: Wi-Fi up but the TutorBox does not answer
    NeedsSecret,        // magenta, fast blink: no secret in flash yet (USB setup)
    Rejected,           // magenta, fast blink: the TutorBox refused the secret
    Unassigned,         // magenta, slow blink: the teacher has not assigned it yet
    Ready               // working: green blip, white when a question is open
  };

  enum class RequestKind : uint8_t { None, Auth, Poll, Heartbeat, Vote };

  struct Request {
    RequestKind kind;
    bool post;           // false: a GET with no body
    const char* bearer;  // the token for the Authorization header, or nullptr
    char path[protocol::kPathSize];
    char body[192];
  };

  typedef void (*LogFn)(const char* line);

  // How often it talks to the TutorBox, by situation (milliseconds).
  static const uint32_t kPollEveryMs = 1000;
  static const uint32_t kHeartbeatEveryMs = 5000;
  static const uint32_t kRetryEveryMs = 2000;
  static const uint32_t kUnassignedEveryMs = 5000;
  static const uint32_t kLockedOutEveryMs = 30000;
  static const uint8_t kFailuresBeforeUnreachable = 3;
  static const uint8_t kVoteAttempts = 3;
  static const uint32_t kVoteRetryMs = 250;

  ClickerApp();
  // `secret` is what flash holds: "" on a clicker that was never set up.
  void begin(const char* deviceId, const char* firmware, const char* secret, LogFn log,
             uint32_t nowMs);

  // ---- what happened ----
  void setWifi(bool connected, uint32_t nowMs);
  void setVitals(int rssi, int batteryPct);
  // A new secret arrived over USB: forget the token and log in with it.
  void setSecret(const char* secret, uint32_t nowMs);
  void onButton(char option, uint32_t nowMs);
  void onResponse(RequestKind kind, int status, const char* body, uint32_t nowMs);

  // ---- what to do ----
  // One request at a time: after it returns true, nothing more until onResponse().
  bool nextRequest(uint32_t nowMs, Request& out);
  StatusLed::Color ledColor(uint32_t nowMs);
  bool statusLedOn(uint32_t nowMs) const;

  Phase phase() const { return phase_; }
  const char* phaseName() const;
  // A question is open, this clicker has not answered it, no vote pending.
  bool armed() const;

 private:
  void onAuth(int status, const char* body, uint32_t nowMs);
  void onPoll(int status, const char* body, uint32_t nowMs);
  void onHeartbeat(int status, const char* body, uint32_t nowMs);
  void onVote(int status, const char* body, uint32_t nowMs);
  void updateRound(const protocol::SessionView& view, uint32_t nowMs);
  void startLogin(uint32_t nowMs);
  void dropToken();
  void countFailure();
  void cancelVote(StatusLed::Color color, uint32_t nowMs);
  void finishVote(bool counted, uint32_t nowMs);
  void enter(Phase phase);
  void logf(const char* format, ...);

  const char* deviceId_;
  const char* firmware_;
  LogFn log_;
  Phase phase_;
  bool wifi_;
  bool inFlight_;  // a request was handed out and its reply has not come back yet
  uint8_t failures_;
  int rssi_;
  int batteryPct_;

  char secret_[protocol::kSecretSize];
  char token_[protocol::kTokenSize];  // RAM only: a restart logs in again
  bool loginRefused_;                 // the secret got a 401: wait for a new one
  uint32_t nextAuthAt_;
  uint32_t nextPollAt_;
  uint32_t nextBeatAt_;

  char sessionId_[protocol::kSessionIdSize];
  char roundId_[protocol::kRoundIdSize];  // current round, as last reported
  bool roundOpen_;
  bool roundSeen_;
  uint32_t roundSeenAt_;                        // when this clicker first saw it open
  char answeredRound_[protocol::kRoundIdSize];  // round this clicker already answered

  bool votePending_;
  char voteOption_;
  char voteSession_[protocol::kSessionIdSize];
  char voteRound_[protocol::kRoundIdSize];
  uint32_t voteResponseMs_;
  uint8_t voteAttempts_;
  uint32_t voteNextAt_;

  StatusLed led_;
};
