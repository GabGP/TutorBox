// How a clicker is named, from the last 3 bytes of its Wi-Fi MAC address: the same
// bytes the router's client list shows, so "ESP32-A4CF12" there and on the case match.
// No Arduino calls in here, so it is unit-tested on a PC (hosttest/).
#pragma once

#include <stdint.h>

#include "../support/FixedText.h"

struct DeviceName
{
  FixedText<16> deviceId; // "ESP32-A4CF12": what the teacher sees and the server keys on
  FixedText<24> hostname; // "clicker-a4cf12": what the router lists
};

// `efuseMac` as ESP.getEfuseMac() returns it: MAC byte 0 in the lowest 8 bits.
DeviceName deviceNameFromMac(uint64_t efuseMac);
