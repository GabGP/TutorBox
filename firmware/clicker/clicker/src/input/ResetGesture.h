// The reset gesture: holding A and D from power-on for RESET_HOLD_MS makes the clicker
// forget its secret. Let go of either button sooner and it is cancelled; one button
// alone never starts it. It is only checked at start-up, before Wi-Fi, so a press during
// a lesson cannot trigger it.
//
// No Arduino calls in here, so it is unit-tested on a PC (hosttest/).
#pragma once

#include <stdint.h>

class ResetGesture
{
public:
  enum class Result : uint8_t
  {
    Idle,      // not running: A and D were not both down at power-on, or it is over
    Holding,   // A and D are both down, and the hold time has not passed yet
    Cancelled, // one of them was let go before the hold time
    Confirmed  // held for the whole hold time: the secret must be forgotten
  };

  explicit ResetGesture(uint32_t holdMs);

  // Call every loop during start-up with the state of buttons A and D, and the time in
  // milliseconds. Returns Holding until the gesture is decided, then the decision once.
  Result update(bool aDown, bool dDown, uint32_t nowMs);

private:
  uint32_t holdMs_;
  bool started_; // update() has run at least once
  bool armed_;   // both were down at the first update(): the gesture may run
  uint32_t heldSinceMs_;
};
