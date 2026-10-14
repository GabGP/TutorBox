// The two lights: the RGB LED the student looks at, and the board's small status LED.
// Pins and LED type come from config.h.
#pragma once

#include "../light/StatusLed.h"

class Lights
{
public:
  // Sets the pins as outputs and switches both lights off.
  void begin();

  // Each writes the pins only when the value changes.
  void showColor(StatusLed::Color color);
  void showStatus(bool on);

private:
  int shownColor_ = -1; // nothing written yet
  int shownStatus_ = -1;
};
