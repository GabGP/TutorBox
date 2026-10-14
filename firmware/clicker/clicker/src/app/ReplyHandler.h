// What each server reply changes: it reads the outcome (protocol/ReplyMeaning.h) and
// passes it to the part it concerns. Connection hears about logins and server health,
// Voting about rounds and votes, Schedule about when to ask again.
#pragma once

#include <stdint.h>

#include "../support/Logger.h"
#include "Connection.h"
#include "Request.h"
#include "Schedule.h"
#include "Voting.h"

class ReplyHandler
{
public:
  ReplyHandler(Logger &log, Connection &connection, Voting &voting, Schedule &schedule);

  // `status` is the HTTP status, or negative when the server did not answer.
  void handle(RequestKind kind, int status, const char *body, uint32_t nowMs);

private:
  void onLogin(int status, const char *body, uint32_t nowMs);
  void onPoll(int status, const char *body, uint32_t nowMs);
  void onHeartbeat(int status, const char *body, uint32_t nowMs);
  void onVote(int status, const char *body, uint32_t nowMs);
  void endSession(uint32_t nowMs);

  Logger &log_;
  Connection &connection_;
  Voting &voting_;
  Schedule &schedule_;
};
