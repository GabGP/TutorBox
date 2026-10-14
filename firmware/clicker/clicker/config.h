// =============================================================================
//  TutorBox clicker: settings
//  Change these if your wiring or network differs from firmware/clicker/README.md
// =============================================================================
#pragma once

// ---- Wi-Fi password ----------------------------------------------------------
// The classroom Wi-Fi name and password live in secrets.h, which git ignores so the
// password never reaches GitHub. First time: copy secrets.example.h to secrets.h.
#if __has_include("secrets.h")
#include "secrets.h"
#else
#error "Missing secrets.h: copy secrets.example.h to secrets.h (same folder) and type the TutorBox Wi-Fi password in it."
#endif

// ---- Where the TutorBox lives --------------------------------------------------
// The Jetson keeps this address on the classroom network (infra/glinet/initial.md
// section 5); nginx answers on port 80. No trailing slash.
#define TUTORBOX_URL "http://192.168.8.2"

// ---- Answer buttons ---------------------------------------------------------------
// Each button connects its pin to GND when pressed. The chip's internal pull-up
// keeps the pin HIGH otherwise, so no resistors are needed.
// Avoid GPIO 2, 8 and 9 (boot pins) and 18-21 (USB / serial) for buttons.
#define PIN_BUTTON_A 0
#define PIN_BUTTON_B 1
#define PIN_BUTTON_C 3
#define PIN_BUTTON_D 10

// ---- RGB LED (the light the student looks at) ------------------------------------
// Common-cathode RGB LED: the longest leg goes to GND, each color leg through its
// own resistor to these pins. If your LED's longest leg must go to 3V3 instead,
// it is common-anode: set LED_COMMON_ANODE to 1.
#define PIN_LED_RED 5
#define PIN_LED_GREEN 6
#define PIN_LED_BLUE 7
#define LED_COMMON_ANODE 0

// ---- Little blue LED soldered on the Super Mini -----------------------------------
// GPIO 8, lit when the pin is LOW. On = Wi-Fi connected, blinking = searching.
// Set PIN_STATUS_LED to -1 if your board has an RGB "NeoPixel" on GPIO 8 instead.
#define PIN_STATUS_LED 8
#define STATUS_LED_ACTIVE_LOW 1

// ---- Battery level (optional) -------------------------------------------------------
// Battery + (after the power switch) -> 100k -> GPIO 4 -> 100k -> GND.
// Leave -1 if you did not fit the two resistors.
#define PIN_BATTERY_SENSE -1
#define BATTERY_DIVIDER 2.0f
// What the teacher's list shows as 0 % and 100 %. These suit one LiPo cell; for a
// 3 x AA box use about 3300 and 4500.
#define BATTERY_EMPTY_MV 3300
#define BATTERY_FULL_MV 4200

// ---- Radio ------------------------------------------------------------------------
// Many ESP32-C3 Super Mini boards lose Wi-Fi at full transmit power (tiny antenna and
// regulator). 8.5 dBm still covers a classroom. Set 0 to use full power.
#define WIFI_LOW_TX_POWER 1
// Modem sleep saves battery between check-ins. Set 0 if votes ever feel slow.
#define WIFI_POWER_SAVE 1

#define FIRMWARE_VERSION "2.0.0"
