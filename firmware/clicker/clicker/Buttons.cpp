#include "Buttons.h"

ButtonBank::ButtonBank(uint16_t debounceMs) : debounceMs_(debounceMs), primed_(false) {
  for (uint8_t i = 0; i < kCount; i++) {
    armed_[i] = false;
    down_[i] = false;
    since_[i] = 0;
    lastEdges_[i] = 0;
  }
}

char ButtonBank::update(const bool pressed[kCount], const uint32_t edges[kCount],
                        uint32_t nowMs) {
  char result = 0;
  for (uint8_t i = 0; i < kCount; i++) {
    // Edges counted before the first call are history, not presses.
    const bool tapped = primed_ && edges[i] != lastEdges_[i];
    lastEdges_[i] = edges[i];
    if (!primed_ || pressed[i] != down_[i]) {
      down_[i] = pressed[i];
      since_[i] = nowMs;
    }
    const bool steady = nowMs - since_[i] >= debounceMs_;

    if (!armed_[i]) {
      // Re-arm only after a steady release. Edges seen meanwhile were contact
      // bounce from the last press or release, and are dropped.
      if (!down_[i] && steady) armed_[i] = true;
      continue;
    }
    const bool held = down_[i] && steady;  // in case the interrupt missed it
    if (tapped || held) {
      armed_[i] = false;
      // Two buttons in the same instant: the first one wins, the other is dropped.
      if (result == 0) result = static_cast<char>('A' + i);
    }
  }
  primed_ = true;
  return result;
}
