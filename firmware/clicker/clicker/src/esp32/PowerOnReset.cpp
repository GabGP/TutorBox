#include "PowerOnReset.h"

#include <Arduino.h>

#include "../../config.h"
#include "../input/ResetGesture.h"

namespace
{

  // Waits while A and D stay down, magenta meanwhile. Returns how the gesture ended.
  ResetGesture::Result waitForDecision(const ButtonPins &buttons, Lights &lights)
  {
    ResetGesture gesture(RESET_HOLD_MS);
    for (;;)
    {
      const ButtonSample sample = buttons.read();
      const ResetGesture::Result result =
          gesture.update(sample.isDown('A'), sample.isDown('D'), millis());
      if (result != ResetGesture::Result::Holding)
        return result;
      lights.showColor(StatusLed::Magenta);
      delay(2);
    }
  }

} // namespace

void resetIfHeldAtPowerOn(const ButtonPins &buttons, Lights &lights, SecretStore &store,
                          Logger::Sink log)
{
  if (waitForDecision(buttons, lights) == ResetGesture::Result::Confirmed)
  {
    lights.showColor(StatusLed::White);
    delay(1000);
    log(store.forget() ? "reset: this clicker will make a new secret"
                       : "reset: flash did not erase the old secret, so it keeps it");
  }
  lights.showColor(StatusLed::Off);
}
