// What the simulator's stand-ins share with each other (not seen by the firmware).
#pragma once

#include <stdint.h>

const int kSimPins = 32;

// The level of each pin (HIGH = a button up), and the interrupt attached to it.
extern int gLevel[kSimPins];
extern void (*gIsr[kSimPins])(void *);
extern void *gIsrArg[kSimPins];

// The simulated MAC (CLICKER_SIM_MAC), most significant byte first.
uint64_t simMac();

// Whether the simulated Wi-Fi is up right now (sim_wifi.cpp).
bool simWifiUp();

// Runs the test's typed commands and ends the timed presses (sim_main.cpp). Called
// before every loop() and from every delay().
void simPumpInput();
