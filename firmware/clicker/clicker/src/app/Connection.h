// The clicker's standing with the Utz'tutor: Wi-Fi, the login, the token, and whether
// the server answers. It owns the Phase. Votes are not its business (Voting.h).
// The login methods are in ConnectionLogin.cpp, the rest in Connection.cpp.
#pragma once

#include <stdint.h>

#include "../device/Secret.h"
#include "../protocol/Protocol.h"
#include "../protocol/ReplyMeaning.h"
#include "../support/Deadline.h"
#include "../support/Logger.h"
#include "Phase.h"

class Connection
{
public:
  enum class WifiChange : uint8_t
  {
    Unchanged,
    Lost,
    Restored
  };

  explicit Connection(Logger &log);
  // `secret` is the clicker's own, from SecretStore. It is never logged.
  void begin(const char *deviceId, const char *secret, uint32_t nowMs);

  Phase phase() const { return phase_; }
  bool wifiUp() const { return wifi_; }
  bool hasToken() const { return !token_.isEmpty(); }
  const char *token() const { return token_.c_str(); }
  const char *deviceId() const { return deviceId_; }
  const char *secret() const { return secret_.c_str(); }
  // Unassigned or rejected: only the teacher, on /maestro/, can fix that.
  bool waitingForTeacher() const;

  // Wi-Fi went up or down. The token outlives a drop: if the Utz'tutor ended it
  // meanwhile, the next heartbeat gets a 401 and the clicker logs in again.
  WifiChange setWifi(bool connected, uint32_t nowMs);

  // Login: due when its time has come, never after a refusal (see askAgain).
  bool loginIsDue(uint32_t nowMs) const;
  void loginSent(uint32_t nowMs);
  void onLoginReply(protocol::LoginOutcome outcome, const protocol::LoginReply &reply,
                    int status, const char *detail, uint32_t nowMs);
  // A button press after a refusal: the only thing that asks a refused clicker again.
  // Every refused login counts toward the lockout: one press is one login, never a
  // timer.
  void askAgain(uint32_t nowMs);
  // The Utz'tutor ended the session (a 401): forget the token and log in again.
  void endSession(uint32_t nowMs);

  // Whether a poll got its answer: enough failures in a row mean "unreachable".
  void serverAnswered();
  void serverFailed();

private:
  void startLogin(uint32_t nowMs);
  void enter(Phase phase) { phase_ = phase; }

  Logger &log_;
  const char *deviceId_;
  Secret secret_;
  protocol::Token token_; // RAM only: a restart logs in again
  Phase phase_;
  bool wifi_;
  bool loginRefused_; // the Utz'tutor refused the login: only a press asks again
  uint8_t failures_;  // requests in a row that got no usable answer
  Deadline nextLogin_;
};
