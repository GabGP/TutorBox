#include "PendingVote.h"

PendingVote::PendingVote() : pending_(false), option_(0), responseMs_(0), attempts_(0) {}

void PendingVote::start(char option, const char *sessionId, const char *roundId,
                        uint32_t responseMs, uint32_t nowMs)
{
  pending_ = true;
  option_ = option;
  sessionId_.assignTruncated(sessionId);
  roundId_.assignTruncated(roundId);
  responseMs_ = responseMs;
  attempts_ = 0;
  nextTry_.dueNow(nowMs);
}
