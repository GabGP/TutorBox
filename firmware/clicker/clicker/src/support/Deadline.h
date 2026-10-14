// Time keeping in millis(), which wraps around to 0 after about 49 days. Both classes
// stay correct across that wrap.
#pragma once

#include <stdint.h>

// The moment something is due: the next poll, the next login, a vote's next try.
class Deadline
{
public:
  Deadline() : dueAtMs_(0) {}

  void dueNow(uint32_t nowMs) { dueAtMs_ = nowMs; }
  void dueIn(uint32_t nowMs, uint32_t delayMs) { dueAtMs_ = nowMs + delayMs; }

  // True once `nowMs` has reached the due moment.
  bool isDue(uint32_t nowMs) const
  {
    return static_cast<int32_t>(nowMs - dueAtMs_) >= 0;
  }

private:
  uint32_t dueAtMs_;
};

// Something that repeats every `periodMs`: the vitals reading, the status line.
class Interval
{
public:
  explicit Interval(uint32_t periodMs) : periodMs_(periodMs), lastMs_(0) {}

  // True when a whole period has passed since the last time; it then starts again.
  bool elapsed(uint32_t nowMs)
  {
    if (nowMs - lastMs_ < periodMs_)
      return false;
    lastMs_ = nowMs;
    return true;
  }

  // Starts a new period now, for something that ran early.
  void restart(uint32_t nowMs) { lastMs_ = nowMs; }

private:
  uint32_t periodMs_;
  uint32_t lastMs_;
};
