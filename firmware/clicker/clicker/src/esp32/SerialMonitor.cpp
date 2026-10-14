#include "SerialMonitor.h"

#include <Arduino.h>

#include "../../config.h"

void startSerialMonitor()
{
  Serial.begin(115200);
  delay(300);
}

void printBanner(const char *deviceId)
{
  Serial.println();
  Serial.println("=========== Utz'tutor clicker ===========");
  Serial.printf("Device id : %s   <- write it on the case\n", deviceId);
  Serial.printf("Firmware  : %s\n", FIRMWARE_VERSION);
  Serial.printf("Wi-Fi     : %s\n", WIFI_SSID);
  Serial.printf("Utz'tutor : %s\n", UTZTUTOR_URL);
  Serial.println("=========================================");
}
