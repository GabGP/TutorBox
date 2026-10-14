#include "StatusLed.h"

namespace
{
  const uint16_t kBlinkOnMs = 150;
  const uint16_t kBlinkOffMs = 150;
  const StatusLed::Pattern kDark = {StatusLed::Off, 0, 0};

  bool samePattern(const StatusLed::Pattern &a, const StatusLed::Pattern &b)
  {
    return a.color == b.color && a.onMs == b.onMs && a.offMs == b.offMs;
  }
} // namespace

StatusLed::StatusLed()
    : background_(kDark),
      backgroundStartMs_(0),
      overlay_(kDark),
      overlayStartMs_(0),
      overlayLengthMs_(0) {}

void StatusLed::setPattern(const Pattern &pattern, uint32_t nowMs)
{
  if (samePattern(pattern, background_))
    return;
  background_ = pattern;
  backgroundStartMs_ = nowMs;
}

void StatusLed::flash(Color color, uint16_t durationMs, uint32_t nowMs)
{
  const Pattern steady = {color, durationMs, 0};
  startOverlay(steady, durationMs, nowMs);
}

void StatusLed::blink(Color color, uint8_t times, uint32_t nowMs)
{
  const Pattern blinking = {color, kBlinkOnMs, kBlinkOffMs};
  // The last blink keeps its dark gap so the background does not look like one more.
  startOverlay(blinking, static_cast<uint32_t>(times) * (kBlinkOnMs + kBlinkOffMs),
               nowMs);
}

bool StatusLed::overlayActive(uint32_t nowMs) const
{
  return overlayLengthMs_ > 0 && nowMs - overlayStartMs_ < overlayLengthMs_;
}

StatusLed::Color StatusLed::colorAt(uint32_t nowMs) const
{
  if (overlayActive(nowMs))
    return colorOf(overlay_, nowMs - overlayStartMs_);
  return colorOf(background_, nowMs - backgroundStartMs_);
}

StatusLed::Color StatusLed::colorOf(const Pattern &pattern, uint32_t elapsedMs)
{
  if (pattern.onMs == 0)
    return Off;
  if (pattern.offMs == 0)
    return pattern.color;
  const uint32_t periodMs = static_cast<uint32_t>(pattern.onMs) + pattern.offMs;
  return (elapsedMs % periodMs) < pattern.onMs ? pattern.color : Off;
}

void StatusLed::startOverlay(const Pattern &pattern, uint32_t lengthMs, uint32_t nowMs)
{
  overlay_ = pattern;
  overlayStartMs_ = nowMs;
  overlayLengthMs_ = lengthMs;
}
