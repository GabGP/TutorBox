// Where the clicker stands with the Utz'tutor. The state machine is drawn in
// docs/architecture/esp32-protocol.md §3; the light for each phase is in LightPlan.cpp.
#pragma once

#include <stdint.h>

enum class Phase : uint8_t
{
  LookingForWifi,    // blue, fast blink
  Connecting,        // blue, steady: Wi-Fi up, logging in to the Utz'tutor
  ServerUnreachable, // blue, slow blink: Wi-Fi up but the Utz'tutor does not answer
  Rejected,          // magenta, fast blink: the Utz'tutor refused the login
  Unassigned,        // magenta, slow blink: the teacher has not assigned it yet
  Ready              // working: green blip, white when a question is open
};

// "looking-for-wifi", "connecting"...: the name the serial status line prints.
const char *phaseName(Phase phase);
