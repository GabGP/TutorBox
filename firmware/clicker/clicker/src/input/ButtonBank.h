// Turns the four answer buttons into clean, single presses: 'A', 'B', 'C' or 'D'.
//
// No Arduino calls in here, so the same code is unit-tested on a PC (hosttest/).
#pragma once

#include <stdint.h>

const uint8_t kButtonCount = 4;

// One reading of the four buttons, index 0 = A ... 3 = D (esp32/ButtonPins.cpp).
struct ButtonSample
{
  bool pressed[kButtonCount];   // is the button down right now?
  uint32_t edges[kButtonCount]; // a counter the pin interrupt bumps on each press, so a
                                // quick tap made while the clicker was busy still counts

  bool isDown(char option) const { return pressed[option - 'A']; }
};

class ButtonBank
{
public:
  explicit ButtonBank(uint16_t debounceMs = 30);

  // Call every loop. Returns 'A'..'D' for a new press, or 0.
  //
  // A button reports one press, then must be released for debounceMs before it can
  // report the next one: contact bounce and long holds never vote twice. Buttons held
  // while the clicker powers on are ignored until released.
  char update(const ButtonSample &sample, uint32_t nowMs);

private:
  uint16_t debounceMs_;
  bool primed_;
  bool armed_[kButtonCount];
  bool down_[kButtonCount];
  uint32_t since_[kButtonCount];     // when the level last changed
  uint32_t lastEdges_[kButtonCount]; // interrupt counter value seen last time
};
