// =============================================================================
//  Utz'tutor clicker: ESP32-C3 firmware
//
//  Power on -> makes its own secret the first time -> joins the Utz'tutor Wi-Fi by
//  itself -> logs in with that secret. The teacher assigns it to a student in
//  Clickers on /maestro/. When a question is open the LED blinks white: press A, B, C
//  or D. Yellow = sending, green = counted, red x3 = not accepted.
//
//  First time? Read firmware/clicker/README.md (wiring, flashing, LED meanings).
//  Settings: config.h. Wi-Fi password: secrets.h (copy secrets.example.h).
//  Reset: hold A and D while switching it on, for 5 seconds (README, section 7).
//
//  This file only wires the parts together. The decisions are in src/app/, the
//  hardware in src/esp32/ (README, section 11).
// =============================================================================
#include "config.h"
#include "src/app/ClickerApp.h"
#include "src/device/DeviceName.h"
#include "src/esp32/BatterySensor.h"
#include "src/esp32/ButtonPins.h"
#include "src/esp32/HttpLink.h"
#include "src/esp32/Lights.h"
#include "src/esp32/PowerOnReset.h"
#include "src/esp32/SecretStore.h"
#include "src/esp32/SerialMonitor.h"
#include "src/esp32/WifiLink.h"
#include "src/input/ButtonBank.h"
#include "src/support/Deadline.h"

static DeviceName deviceName;
static Lights lights;
static ButtonPins buttonPins;
static ButtonBank buttons;
static WifiLink wifi;
static SecretStore secretStore;
static HttpLink http;
static ClickerApp app;

static Interval vitalsEvery(5000);  // signal strength and battery
static Interval statusEvery(15000); // the status line on the serial monitor

static void logLine(const char *line)
{
  Serial.printf("[%s] %s\n", deviceName.deviceId.c_str(), line);
}

void setup()
{
  startSerialMonitor();
  lights.begin();
  buttonPins.begin();
  deviceName = deviceNameFromMac(ESP.getEfuseMac());
  printBanner(deviceName.deviceId.c_str());
  http.begin();
  resetIfHeldAtPowerOn(buttonPins, lights, secretStore, logLine);
  // The radio first: esp_random() is only truly random while it is on.
  wifi.start(deviceName.hostname.c_str());
  secretStore.loadOrCreate(); // this clicker's own secret: made once, kept in flash
  app.begin(deviceName.deviceId.c_str(), FIRMWARE_VERSION, secretStore.secret(), logLine,
            millis());
}

// 1. Wi-Fi: keep it up and tell the app whether it is. Signal and battery are read
//    every 5 s, and right when Wi-Fi comes or goes, so the first heartbeat has them.
static bool feedWifi(uint32_t nowMs)
{
  static bool wasConnected = false;
  wifi.maintain(nowMs);
  const bool connected = wifi.connected();
  if (connected != wasConnected || vitalsEvery.elapsed(nowMs))
  {
    wasConnected = connected;
    vitalsEvery.restart(nowMs);
    app.setVitals(wifi.rssi(), readBatteryPercent());
  }
  app.setWifi(connected, nowMs);
  return connected;
}

// 2. Buttons: a clean press becomes 'A'..'D'.
static void feedButtons(uint32_t nowMs)
{
  const char option = buttons.update(buttonPins.read(), nowMs);
  if (option != 0)
    app.onButton(option, nowMs);
}

// 3. Network: at most one request per loop (login, poll, heartbeat or vote).
static void exchangeOneRequest(uint32_t nowMs)
{
  static String reply;
  Request request;
  if (!app.nextRequest(nowMs, request))
    return;
  const int status = http.send(request, reply);
  app.onResponse(request.kind, status, reply.c_str(), millis());
}

// 4. Lights, at the time they are shown (the request may have taken a while).
static void showLights()
{
  const uint32_t nowMs = millis();
  lights.showColor(app.ledColor(nowMs));
  lights.showStatus(app.statusLedOn(nowMs));
}

// 5. A status line every 15 s, for whoever has the serial monitor open.
static void reportStatus(uint32_t nowMs, bool wifiConnected)
{
  if (!statusEvery.elapsed(nowMs))
    return;
  Serial.printf("[%s] status: %s, Wi-Fi %s, signal %d dBm\n", deviceName.deviceId.c_str(),
                app.phaseName(), wifiConnected ? "on" : "off", wifi.rssi());
}

void loop()
{
  const uint32_t nowMs = millis();
  const bool wifiConnected = feedWifi(nowMs);
  feedButtons(nowMs);
  exchangeOneRequest(nowMs);
  showLights();
  reportStatus(nowMs, wifiConnected);
  delay(2);
}
