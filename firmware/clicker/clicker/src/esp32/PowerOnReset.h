// The reset gesture, checked once at power-on, before Wi-Fi starts: A and D held for
// RESET_HOLD_MS (config.h) make the clicker forget its secret. The rule itself is in
// input/ResetGesture. The light is the only thing that shows it: magenta while held,
// white for a second once the secret is forgotten.
#pragma once

#include "../support/Logger.h"
#include "ButtonPins.h"
#include "Lights.h"
#include "SecretStore.h"

// Returns at once when A and D are not both down at power-on.
void resetIfHeldAtPowerOn(const ButtonPins &buttons, Lights &lights, SecretStore &store,
                          Logger::Sink log);
