#include "RoundTracker.h"

RoundTracker::RoundTracker() : open_(false), noticed_(false), noticedAtMs_(0) {}

void RoundTracker::follow(const protocol::SessionView &view)
{
  sessionId_.assignTruncated(view.sessionId.c_str());
  if (!roundId_.equals(view.roundId.c_str()))
  {
    roundId_.assignTruncated(view.roundId.c_str());
    noticed_ = false;
  }
  open_ = view.roundOpen;
}

void RoundTracker::forgetOpenRound() { open_ = false; }

bool RoundTracker::waitingForAnswer() const
{
  return open_ && !roundId_.isEmpty() && !roundId_.equals(answeredRoundId_.c_str());
}

void RoundTracker::notice(uint32_t nowMs)
{
  noticed_ = true;
  noticedAtMs_ = nowMs;
}

void RoundTracker::markAnswered(const char *roundId)
{
  answeredRoundId_.assignTruncated(roundId);
}
