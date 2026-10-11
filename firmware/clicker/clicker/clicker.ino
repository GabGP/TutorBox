// =============================================================================
//  TutorBox clicker: ESP32-C3 firmware
//
//  Power on -> joins the TutorBox Wi-Fi by itself -> checks in every second.
//  When the teacher opens a question the LED blinks white: press A, B, C or D.
//  Yellow = sending, green = counted, red x3 = not accepted.
//
//  First time? Read firmware/clicker/README.md (wiring, flashing, LED meanings).
//  Settings: config.h. Wi-Fi password: secrets.h (copy secrets.example.h).
// =============================================================================
#include "Board.h"
#include "Buttons.h"
#include "ClickerApp.h"
#include "config.h"

static Board board;
static ButtonBank buttons;
static ClickerApp app;

static void logLine(const char* line) {
  Serial.printf("[%s] %s\n", board.deviceId(), line);
}

void setup() {
  board.begin();
  app.begin(board.deviceId(), FIRMWARE_VERSION, logLine, millis());
}

void loop() {
  static uint32_t lastVitalsMs = 0;
  static uint32_t lastReportMs = 0;
  static bool lastWifi = false;
  static char reply[512];
  const uint32_t now = millis();

  // 1. Wi-Fi: keep it up, tell the app whether it is. Signal and battery are read
  //    every 5 s, and right when Wi-Fi comes up so the first check-in has them.
  board.maintainWifi(now);
  const bool wifi = board.wifiConnected();
  if (wifi != lastWifi || now - lastVitalsMs >= 5000) {
    lastWifi = wifi;
    lastVitalsMs = now;
    app.setVitals(board.rssi(), board.batteryMv());
  }
  app.setWifi(wifi, now);

  // 2. Buttons: a clean press becomes 'A'..'D'.
  bool pressed[ButtonBank::kCount];
  uint32_t edges[ButtonBank::kCount];
  board.readButtons(pressed, edges);
  const char option = buttons.update(pressed, edges, now);
  if (option != 0) app.onButton(option, now);

  // 3. Network: at most one request per loop (a check-in or a vote).
  ClickerApp::Request request;
  if (app.nextRequest(now, request)) {
    const int status = board.post(request.path, request.body, reply, sizeof(reply));
    app.onResponse(request.kind, status, reply, millis());
  }

  // 4. Lights.
  board.showColor(app.ledColor(millis()));
  board.showStatus(app.statusLedOn(millis()));

  if (now - lastReportMs >= 15000) {
    lastReportMs = now;
    Serial.printf("[%s] status: %s, Wi-Fi %s, signal %d dBm\n", board.deviceId(),
                  app.phaseName(), wifi ? "on" : "off", board.rssi());
  }
  delay(2);
}
