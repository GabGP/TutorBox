#include "Lights.h"

#include <Arduino.h>

#include "../../config.h"

namespace
{
  // A common-anode LED lights when its pin is LOW, a common-cathode one when HIGH.
  const uint8_t kColorOn = LED_COMMON_ANODE ? LOW : HIGH;
  const uint8_t kColorOff = LED_COMMON_ANODE ? HIGH : LOW;

  void writeColorLeg(uint8_t pin, bool lit)
  {
    digitalWrite(pin, lit ? kColorOn : kColorOff);
  }
} // namespace

void Lights::begin()
{
  pinMode(PIN_LED_RED, OUTPUT);
  pinMode(PIN_LED_GREEN, OUTPUT);
  pinMode(PIN_LED_BLUE, OUTPUT);
  showColor(StatusLed::Off);
#if PIN_STATUS_LED >= 0
  pinMode(PIN_STATUS_LED, OUTPUT);
  showStatus(false);
#endif
}

void Lights::showColor(StatusLed::Color color)
{
  if (static_cast<int>(color) == shownColor_)
    return;
  shownColor_ = color;
  writeColorLeg(PIN_LED_RED, (color & StatusLed::Red) != 0);
  writeColorLeg(PIN_LED_GREEN, (color & StatusLed::Green) != 0);
  writeColorLeg(PIN_LED_BLUE, (color & StatusLed::Blue) != 0);
}

void Lights::showStatus(bool on)
{
#if PIN_STATUS_LED >= 0
  if (static_cast<int>(on) == shownStatus_)
    return;
  shownStatus_ = on;
  // An active-low LED lights when its pin is LOW.
  digitalWrite(PIN_STATUS_LED, (on != (STATUS_LED_ACTIVE_LOW != 0)) ? HIGH : LOW);
#else
  (void)on;
#endif
}
