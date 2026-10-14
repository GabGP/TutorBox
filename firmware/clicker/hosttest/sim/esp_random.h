// PC stand-in for the ESP32 random number generator (esp_random.h of Arduino-ESP32 3.x).
// The simulator answers from the host's random source, so two simulated clickers make
// different secrets.
#pragma once

#include <stdint.h>

#ifdef __cplusplus
extern "C"
{
#endif

  uint32_t esp_random(void);

#ifdef __cplusplus
}
#endif
