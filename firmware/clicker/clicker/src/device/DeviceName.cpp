#include "DeviceName.h"

#include <stdio.h>

DeviceName deviceNameFromMac(uint64_t efuseMac)
{
  const uint8_t byte3 = static_cast<uint8_t>(efuseMac >> 24);
  const uint8_t byte4 = static_cast<uint8_t>(efuseMac >> 32);
  const uint8_t byte5 = static_cast<uint8_t>(efuseMac >> 40);
  DeviceName name;
  snprintf(name.deviceId.buffer(), name.deviceId.capacity(), "ESP32-%02X%02X%02X", byte3,
           byte4, byte5);
  snprintf(name.hostname.buffer(), name.hostname.capacity(), "clicker-%02x%02x%02x",
           byte3, byte4, byte5);
  return name;
}
