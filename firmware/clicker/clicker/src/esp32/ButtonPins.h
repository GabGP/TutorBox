// The four answer buttons' pins (config.h). Each pin has an interrupt that counts
// presses, so a tap made while the loop waits on the network still counts.
// The rules for what makes a press live in input/ButtonBank.
#pragma once

#include "../input/ButtonBank.h"

class ButtonPins
{
public:
  // Pull-ups on, interrupts attached.
  void begin();
  ButtonSample read() const;
};
