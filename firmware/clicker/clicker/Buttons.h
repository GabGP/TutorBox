// Turns the four answer buttons into clean, single presses: 'A', 'B', 'C' or 'D'.
//
// No Arduino calls in here, so the same code is unit-tested on a PC (hosttest/).
#pragma once

#include <stdint.h>

class ButtonBank {
 public:
  static const uint8_t kCount = 4;

  explicit ButtonBank(uint16_t debounceMs = 30);

  // Call every loop with:
  //   pressed[i] - is button i down right now?
  //   edges[i]   - a counter the pin interrupt bumps on each press, so a quick tap
  //                made while the clicker was busy on the network still counts.
  // Returns 'A'..'D' for a new press, or 0.
  //
  // A button reports one press, then must be released for debounceMs before it can
  // report the next one: contact bounce and long holds never vote twice. Buttons held
  // while the clicker powers on are ignored until released.
  char update(const bool pressed[kCount], const uint32_t edges[kCount],
              uint32_t nowMs);

 private:
  uint16_t debounceMs_;
  bool primed_;
  bool armed_[kCount];
  bool down_[kCount];
  uint32_t since_[kCount];      // when the level last changed
  uint32_t lastEdges_[kCount];  // interrupt counter value seen last time
};
