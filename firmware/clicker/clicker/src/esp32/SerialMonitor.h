// The serial monitor (115200 baud): where the clicker tells a person what it is doing.
#pragma once

// Opens the port and waits a moment, so a USB monitor can reattach after a reset.
void startSerialMonitor();

// The start-up banner: device id (to write on the case), firmware, Wi-Fi, Utz'tutor.
void printBanner(const char *deviceId);
