// =============================================================================
//  TutorBox clicker: ESP32-C3 firmware
//
//  Power on -> joins the TutorBox Wi-Fi by itself -> logs in with its secret.
//  When the teacher opens a question the LED blinks white: press A, B, C or D.
//  Yellow = sending, green = counted, red x3 = not accepted.
//
//  First time? Read firmware/clicker/README.md (wiring, flashing, LED meanings).
//  Settings: config.h. Wi-Fi password: secrets.h (copy secrets.example.h).
//  The clicker's own secret arrives over USB: README, section "USB setup".
// =============================================================================
#include "Board.h"
#include "Buttons.h"
#include "ClickerApp.h"
#include "SerialSetup.h"
#include "config.h"

static Board board;
static ButtonBank buttons;
static ClickerApp app;
static SerialSetup setupLink;

static void logLine(const char* line) {
  Serial.printf("[%s] %s\n", board.deviceId(), line);
}

// The USB setup link (SerialSetup.h). Its answers start with "clicker-" so the
// tool can tell them from the log. The secret is never printed.
static void handleSetupLink(uint32_t now) {
  for (int c = board.readSerialByte(); c >= 0; c = board.readSerialByte()) {
    switch (setupLink.feed(static_cast<char>(c))) {
      case SerialSetup::Command::Identify:
        Serial.printf("clicker-id %s\n", board.deviceId());
        break;
      case SerialSetup::Command::Secret:
        if (board.storeSecret(setupLink.secret())) {
          app.setSecret(board.secret(), now);
          Serial.println("clicker-secret stored");
        } else {
          Serial.println("clicker-secret failed: flash did not keep it");
        }
        setupLink.forget();
        break;
      case SerialSetup::Command::BadSecret:
        Serial.println("clicker-secret invalid: it is 32 lowercase hex characters");
        break;
      case SerialSetup::Command::Unknown:
        Serial.println("clicker-setup unknown command: use id, or secret <32 hex>");
        break;
      case SerialSetup::Command::None:
        break;
    }
  }
}

void setup() {
  board.begin();
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

  // 2. USB: a secret may arrive while the clicker sits on the teacher's desk.
  handleSetupLink(now);

  // 3. Buttons: a clean press becomes 'A'..'D'.
  bool pressed[ButtonBank::kCount];
  uint32_t edges[ButtonBank::kCount];
  board.readButtons(pressed, edges);
  const char option = buttons.update(pressed, edges, now);
  if (option != 0) app.onButton(option, now);

  // 4. Network: at most one request per loop (login, poll, heartbeat or vote).
  ClickerApp::Request request;
  if (app.nextRequest(now, request)) {
    const int status = board.send(request, reply);
    app.onResponse(request.kind, status, reply.c_str(), millis());
  }

  // 5. Lights.
  board.showColor(app.ledColor(millis()));
  board.showStatus(app.statusLedOn(millis()));

  if (now - lastReportMs >= 15000) {
    lastReportMs = now;
    Serial.printf("[%s] status: %s, Wi-Fi %s, signal %d dBm\n", board.deviceId(),
                  app.phaseName(), wifi ? "on" : "off", board.rssi());
  }
  delay(2);
}
