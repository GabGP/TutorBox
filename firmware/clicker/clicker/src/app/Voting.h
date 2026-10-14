// Questions and answers: which round is open, the vote being sent, and the light the
// student sees after a press. Only used while the Connection is Ready; logging in is
// not its business (Connection.h).
#pragma once

#include <stdint.h>

#include "../light/StatusLed.h"
#include "../protocol/Protocol.h"
#include "../support/Logger.h"
#include "PendingVote.h"
#include "Request.h"
#include "RoundTracker.h"

class Voting
{
public:
  // What the caller must do after a vote reply.
  enum class Next : uint8_t
  {
    Nothing,
    RefreshRound,
    LogInAgain
  };

  Voting(Logger &log, StatusLed &led);

  bool isSending() const { return vote_.isPending(); }
  // A question is open, this clicker has not answered it, and no vote is being sent.
  bool waitingForAnswer() const;
  bool roundIsOpen() const { return rounds_.isOpen(); }

  // The poll's news about the running match.
  void followMatch(const protocol::SessionView &view, uint32_t nowMs);
  void forgetOpenRound() { rounds_.forgetOpenRound(); }

  // A button press while the connection is Ready: a vote, or red x3 when no question
  // waits for an answer.
  void press(char option, uint32_t nowMs);

  bool tryIsDue(uint32_t nowMs) const { return vote_.tryIsDue(nowMs); }
  void makeRequest(Request &out, const char *token);
  Next onVoteReply(int status, const char *body, uint32_t nowMs);

  // A vote that can no longer go out is dropped and shown, never sent late.
  void dropForNoWifi(uint32_t nowMs);
  void dropForNoSession(StatusLed::Color color, uint32_t nowMs);

private:
  void finish(bool counted, uint32_t nowMs);
  void drop(StatusLed::Color color, uint32_t nowMs);

  Logger &log_;
  StatusLed &led_;
  RoundTracker rounds_;
  PendingVote vote_;
};
