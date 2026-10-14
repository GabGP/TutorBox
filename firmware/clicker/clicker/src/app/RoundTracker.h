// Which question (round) the match is on, whether it is open, and whether this clicker
// already answered it. Fed by the poll every second.
#pragma once

#include <stdint.h>

#include "../protocol/Protocol.h"

class RoundTracker
{
public:
  RoundTracker();

  // Takes what the poll reported about the running match.
  void follow(const protocol::SessionView &view);
  // No match is running, or what the clicker knew is too old to trust (Wi-Fi was lost,
  // the session ended): treat the round as closed until the next poll.
  void forgetOpenRound();

  bool isOpen() const { return open_; }
  // An open round that this clicker has not answered yet.
  bool waitingForAnswer() const;

  // The clicker notices a round once, when it first sees it waiting for an answer:
  // it logs it, and the vote's response time counts from then.
  bool noticed() const { return noticed_; }
  void notice(uint32_t nowMs);
  uint32_t msSinceNoticed(uint32_t nowMs) const { return nowMs - noticedAtMs_; }

  const char *sessionId() const { return sessionId_.c_str(); }
  const char *roundId() const { return roundId_.c_str(); }

  // Done with that round, whether the vote counted or not: no second vote in it.
  void markAnswered(const char *roundId);

private:
  protocol::SessionId sessionId_;
  protocol::RoundId roundId_; // the current round, as last reported
  bool open_;
  bool noticed_;
  uint32_t noticedAtMs_;
  protocol::RoundId answeredRoundId_;
};
