// Decides which color the RGB LED shows at each moment.
//
// A background pattern follows the clicker's state (blue blinking while it looks for
// Wi-Fi, white when a question is open...). Short "overlays" such as green for 1.5 s
// after a vote play on top and then hand the background back.
// No Arduino calls in here, so it is unit-tested on a PC (hosttest/).
#pragma once

#include <stdint.h>

class StatusLed
{
public:
  // Bit 0 = red, bit 1 = green, bit 2 = blue: each LED leg is simply on or off.
  enum Color : uint8_t
  {
    Off = 0,
    Red = 1,
    Green = 2,
    Yellow = 3, // red + green
    Blue = 4,
    Magenta = 5, // red + blue
    Cyan = 6,    // green + blue
    White = 7
  };

  // `onMs` lit, then `offMs` dark, repeating. offMs == 0 means steady; onMs == 0, dark.
  struct Pattern
  {
    Color color;
    uint16_t onMs;
    uint16_t offMs;
  };

  StatusLed();

  // The background. Setting the same pattern again keeps the blink rhythm going.
  void setPattern(const Pattern &pattern, uint32_t nowMs);

  // Overlays: steady `color` for durationMs, or `times` short blinks (150/150 ms).
  void flash(Color color, uint16_t durationMs, uint32_t nowMs);
  void blink(Color color, uint8_t times, uint32_t nowMs);

  Color colorAt(uint32_t nowMs) const;
  bool overlayActive(uint32_t nowMs) const;

private:
  static Color colorOf(const Pattern &pattern, uint32_t elapsedMs);
  void startOverlay(const Pattern &pattern, uint32_t lengthMs, uint32_t nowMs);

  Pattern background_;
  uint32_t backgroundStartMs_;
  Pattern overlay_;
  uint32_t overlayStartMs_;
  uint32_t overlayLengthMs_; // 0 = no overlay
};
