// The vote being sent: what was pressed, for which round, and how many tries so far.
// It holds the session and round of the moment of the press, so a vote is never sent
// to a round that opened later.
#pragma once

#include <stdint.h>

#include "../protocol/Protocol.h"
#include "../support/Deadline.h"

class PendingVote
{
public:
  PendingVote();

  bool isPending() const { return pending_; }
  void start(char option, const char *sessionId, const char *roundId,
             uint32_t responseMs, uint32_t nowMs);
  void clear() { pending_ = false; }

  // The next try may go out (the first goes at once, a retry after a pause).
  bool tryIsDue(uint32_t nowMs) const { return pending_ && nextTry_.isDue(nowMs); }
  void countTry() { attempts_++; }
  void retryIn(uint32_t nowMs, uint32_t delayMs) { nextTry_.dueIn(nowMs, delayMs); }
  uint8_t attempts() const { return attempts_; }

  char option() const { return option_; }
  const char *sessionId() const { return sessionId_.c_str(); }
  const char *roundId() const { return roundId_.c_str(); }
  uint32_t responseMs() const { return responseMs_; }

private:
  bool pending_;
  char option_;
  protocol::SessionId sessionId_;
  protocol::RoundId roundId_;
  uint32_t responseMs_; // from noticing the question to the press
  uint8_t attempts_;
  Deadline nextTry_;
};
