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
// =============================================================================
#include "Board.h"
#include "Buttons.h"
#include "ClickerApp.h"
#include "ResetGesture.h"
#include "config.h"

static Board board;
static ButtonBank buttons;
static ClickerApp app;

static void logLine(const char* line) {
  Serial.printf("[%s] %s\n", board.deviceId(), line);
}

// Holding A and D from power-on (ResetGesture.h). It runs before Wi-Fi starts, so the
// light is the only thing that shows it: magenta while held, white for a second once
// the secret is forgotten.
static void resetIfHeld() {
  ResetGesture gesture(RESET_HOLD_MS);
  ResetGesture::Result result = ResetGesture::Result::Idle;
  do {
    bool pressed[ButtonBank::kCount];
    uint32_t edges[ButtonBank::kCount];
    board.readButtons(pressed, edges);
    result = gesture.update(pressed[0], pressed[3], millis());  // 0 = A, 3 = D
    if (result == ResetGesture::Result::Holding) {
      board.showColor(StatusLed::Magenta);
      delay(2);
    }
  } while (result == ResetGesture::Result::Holding);

  if (result == ResetGesture::Result::Confirmed) {
    board.showColor(StatusLed::White);
    delay(1000);
    if (board.resetSecret()) {
      logLine("reset: this clicker will make a new secret");
    } else {
      logLine("reset: flash did not erase the old secret, so it keeps it");
    }
  }
  board.showColor(StatusLed::Off);
}

void setup() {
  board.begin();  // pins, button interrupts, device id, banner
  resetIfHeld();
  // The radio first: esp_random() is only truly random while it is on.
  board.startWifi();
  board.loadOrCreateSecret();  // this clicker's own secret: made once, kept in flash
  app.begin(board.deviceId(), FIRMWARE_VERSION, board.secret(), logLine, millis());
}

void loop() {
  static uint32_t lastVitalsMs = 0;
  static uint32_t lastReportMs = 0;
  static bool lastWifi = false;
  static String reply;
  const uint32_t now = millis();

  // 1. Wi-Fi: keep it up, tell the app whether it is. Signal and battery are read
  //    every 5 s, and right when Wi-Fi comes up so the first heartbeat has them.
  board.maintainWifi(now);
  const bool wifi = board.wifiConnected();
  if (wifi != lastWifi || now - lastVitalsMs >= 5000) {
    lastWifi = wifi;
    lastVitalsMs = now;
    app.setVitals(board.rssi(), board.batteryPct());
  }
  app.setWifi(wifi, now);

  // 2. Buttons: a clean press becomes 'A'..'D'.
  bool pressed[ButtonBank::kCount];
  uint32_t edges[ButtonBank::kCount];
  board.readButtons(pressed, edges);
  const char option = buttons.update(pressed, edges, now);
  if (option != 0) app.onButton(option, now);

  // 3. Network: at most one request per loop (login, poll, heartbeat or vote).
  ClickerApp::Request request;
  if (app.nextRequest(now, request)) {
    const int status = board.send(request, reply);
    app.onResponse(request.kind, status, reply.c_str(), millis());
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
