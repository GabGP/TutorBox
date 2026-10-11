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
    Connecting,         // blue, steady: Wi-Fi up, waiting for the first check-in
    ServerUnreachable,  // blue, slow blink: Wi-Fi up but the TutorBox does not answer
    Rejected,           // magenta, fast blink: the TutorBox refused this clicker
    Unassigned,         // magenta, slow blink: the teacher has not assigned it yet
    Ready               // working: green blip, white when a question is open
  };

  enum class RequestKind : uint8_t { None, Checkin, Vote };

  struct Request {
    RequestKind kind;
    const char* path;
    char body[192];
  };

  typedef void (*LogFn)(const char* line);

  // How often it checks in, by situation (milliseconds).
  static const uint32_t kCheckinEveryMs = 1000;
  static const uint32_t kRetryEveryMs = 2000;
  static const uint32_t kRejectedEveryMs = 5000;
  static const uint8_t kFailuresBeforeUnreachable = 3;
  static const uint8_t kVoteAttempts = 3;
  static const uint32_t kVoteRetryMs = 250;

  ClickerApp();
  void begin(const char* deviceId, const char* firmware, LogFn log, uint32_t nowMs);

  // ---- what happened ----
  void setWifi(bool connected, uint32_t nowMs);
  void setVitals(int rssi, int batteryMv);
  void onButton(char option, uint32_t nowMs);
  void onResponse(RequestKind kind, int status, const char* body, uint32_t nowMs);

  // ---- what to do ----
  // One request at a time: after it returns true, nothing more until onResponse().
  bool nextRequest(uint32_t nowMs, Request& out);
  StatusLed::Color ledColor(uint32_t nowMs);
  bool statusLedOn(uint32_t nowMs) const;

  Phase phase() const { return phase_; }
  const char* phaseName() const;
  // A question is open, this clicker's student has not answered it, no vote pending.
  bool armed() const;

 private:
  void onCheckin(int status, const char* body, uint32_t nowMs);
  void onVote(int status, const char* body, uint32_t nowMs);
  void updateRound(const protocol::CheckinReply& reply, uint32_t nowMs);
  void enter(Phase phase);
  void finishVote(bool counted, uint32_t nowMs);
  void logf(const char* format, ...);

  const char* deviceId_;
  const char* firmware_;
  LogFn log_;
  Phase phase_;
  bool wifi_;
  bool inFlight_;  // a request was handed out and its reply has not come back yet
  uint8_t failures_;
  uint32_t nextCheckinAt_;
  int rssi_;
  int batteryMv_;

  char roundId_[protocol::kRoundIdSize];  // current round, as last reported
  bool roundOpen_;
  bool votedOnServer_;
  bool roundSeen_;
  uint32_t roundSeenAt_;                        // when this clicker first saw it open
  char answeredRound_[protocol::kRoundIdSize];  // round this clicker already answered

  bool votePending_;
  char voteOption_;
  char voteRound_[protocol::kRoundIdSize];
  uint32_t voteResponseMs_;
  uint8_t voteAttempts_;
  uint32_t voteNextAt_;

  StatusLed led_;
};
