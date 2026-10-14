// What the lights show for each situation (README §8 lists them for students).
#pragma once

#include <stdint.h>

#include "../light/StatusLed.h"
#include "Phase.h"

namespace light_plan
{

  // "No": a press that sends nothing, or a vote that was not counted.
  const uint8_t kNoBlinks = 3;
  // "Yes": a vote the Utz'tutor counted.
  const uint16_t kCountedFlashMs = 1500;

  // The RGB LED's background for the phase. In Ready it also tells a vote being sent
  // (yellow) from a question waiting for an answer (white) from idle (green blip).
  StatusLed::Pattern backgroundFor(Phase phase, bool votePending, bool questionWaiting);

  // The board's small LED: steady with Wi-Fi, blinking without.
  bool statusLedOn(bool wifiConnected, uint32_t nowMs);

} // namespace light_plan
