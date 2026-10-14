#include "ResetGesture.h"

ResetGesture::ResetGesture(uint32_t holdMs)
    : holdMs_(holdMs), started_(false), armed_(false), heldSinceMs_(0) {}

ResetGesture::Result ResetGesture::update(bool aDown, bool dDown, uint32_t nowMs) {
  if (!started_) {
    // The first call is the power-on state. A gesture that is not already under way
    // when the clicker starts is off until the next power-on.
    started_ = true;
    armed_ = aDown && dDown;
    heldSinceMs_ = nowMs;
  }
  if (!armed_) return Result::Idle;
  if (!aDown || !dDown) {
    armed_ = false;  // let go before the hold time: cancelled, and not restarted
    return Result::Cancelled;
  }
  // Unsigned subtraction: still right when millis() wraps around after 49 days.
  if (nowMs - heldSinceMs_ >= holdMs_) {
    armed_ = false;
    return Result::Confirmed;
  }
  return Result::Holding;
}
