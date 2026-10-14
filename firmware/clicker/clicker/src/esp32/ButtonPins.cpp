#include "ButtonPins.h"

#include <Arduino.h>

#include "../../config.h"

namespace
{

  // Bumped by the button interrupt, read by loop(). Both arrays are plain globals so
  // they live in RAM: an interrupt must not read flash (flash can be busy).
  volatile uint32_t gEdges[kButtonCount] = {0, 0, 0, 0};
  uint8_t gButtonPins[kButtonCount] = {PIN_BUTTON_A, PIN_BUTTON_B, PIN_BUTTON_C,
                                       PIN_BUTTON_D};

  void ARDUINO_ISR_ATTR onButtonEdge(void *arg)
  {
    const uintptr_t index = reinterpret_cast<uintptr_t>(arg);
    // Count it only if the pin is still LOW: this drops electrical spikes shorter than
    // the few microseconds it takes to get here.
    if (digitalRead(gButtonPins[index]) == LOW)
    {
      gEdges[index] = gEdges[index] + 1;
    }
  }

} // namespace

void ButtonPins::begin()
{
  for (uint8_t i = 0; i < kButtonCount; i++)
  {
    // Each button connects its pin to GND, so a pressed button reads LOW.
    pinMode(gButtonPins[i], INPUT_PULLUP);
    attachInterruptArg(gButtonPins[i], onButtonEdge,
                       reinterpret_cast<void *>(static_cast<uintptr_t>(i)), FALLING);
  }
}

ButtonSample ButtonPins::read() const
{
  ButtonSample sample;
  for (uint8_t i = 0; i < kButtonCount; i++)
  {
    sample.pressed[i] = digitalRead(gButtonPins[i]) == LOW;
    sample.edges[i] = gEdges[i];
  }
  return sample;
}
