#include "StatusLed.h"

namespace {
const uint16_t kBlinkOnMs = 150;
const uint16_t kBlinkOffMs = 150;
}  // namespace

StatusLed::StatusLed()
    : color_(Off),
      onMs_(0),
      offMs_(0),
      patternStart_(0),
      overlayColor_(Off),
      overlayOn_(0),
      overlayOff_(0),
      overlayStart_(0),
      overlayLength_(0) {}

void StatusLed::setPattern(Color color, uint16_t onMs, uint16_t offMs,
                           uint32_t nowMs) {
  if (color == color_ && onMs == onMs_ && offMs == offMs_) return;
  color_ = color;
  onMs_ = onMs;
  offMs_ = offMs;
  patternStart_ = nowMs;
}

void StatusLed::flash(Color color, uint16_t durationMs, uint32_t nowMs) {
  overlayColor_ = color;
  overlayOn_ = durationMs;
  overlayOff_ = 0;
  overlayStart_ = nowMs;
  overlayLength_ = durationMs;
}

void StatusLed::blink(Color color, uint8_t times, uint32_t nowMs) {
  overlayColor_ = color;
  overlayOn_ = kBlinkOnMs;
  overlayOff_ = kBlinkOffMs;
  overlayStart_ = nowMs;
  // The last blink keeps its dark gap so the background does not look like a 4th.
  overlayLength_ = static_cast<uint32_t>(times) * (kBlinkOnMs + kBlinkOffMs);
}

bool StatusLed::overlayActive(uint32_t nowMs) const {
  return overlayLength_ > 0 && nowMs - overlayStart_ < overlayLength_;
}

StatusLed::Color StatusLed::colorAt(uint32_t nowMs) const {
  if (overlayActive(nowMs)) {
    return phaseColor(overlayColor_, overlayOn_, overlayOff_, nowMs - overlayStart_);
  }
  return phaseColor(color_, onMs_, offMs_, nowMs - patternStart_);
}

StatusLed::Color StatusLed::phaseColor(Color color, uint16_t onMs, uint16_t offMs,
                                       uint32_t elapsedMs) {
  if (onMs == 0) return Off;
  if (offMs == 0) return color;
  const uint32_t period = static_cast<uint32_t>(onMs) + offMs;
  return (elapsedMs % period) < onMs ? color : Off;
}
