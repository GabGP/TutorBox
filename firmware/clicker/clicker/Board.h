// Everything that touches the ESP32 hardware: pins, Wi-Fi, HTTP and flash storage.
// The decisions live in ClickerApp; this file only does what it is told.
#pragma once

#include <Arduino.h>
#include <HTTPClient.h>
#include <WiFi.h>

#include "Buttons.h"
#include "ClickerApp.h"
#include "StatusLed.h"

class Board {
 public:
  // Pins, button interrupts, identity (device id + the secret in flash) and Wi-Fi.
  void begin();

  const char* deviceId() const { return deviceId_; }
  // The secret the TutorBox issued to this clicker, "" until it is set up over USB.
  const char* secret() const { return secret_; }
  // Keeps a new secret in flash, so it survives power-off. False if flash refused it.
  bool storeSecret(const char* secret);

  bool wifiConnected() const;
  // Keeps Wi-Fi alive: re-joins after 20 s offline, restarts after 3 minutes.
  void maintainWifi(uint32_t nowMs);
  int rssi() const;
  // Battery as 0..100, or -1 when the two sense resistors are not fitted.
  int batteryPct() const;

  void readButtons(bool pressed[ButtonBank::kCount],
                   uint32_t edges[ButtonBank::kCount]) const;

  // The next byte typed on the USB serial port, or -1 when there is none.
  int readSerialByte();

  // Sends the request to TUTORBOX_URL + path. Returns the HTTP status, or a negative
  // HTTPClient error when the server could not be reached. `reply` gets the body.
  int send(const ClickerApp::Request& request, String& reply);

  void showColor(StatusLed::Color color);
  void showStatus(bool on);

 private:
  void loadSecret();
  void startWifi();

  char deviceId_[16];
  char hostname_[24];
  char secret_[protocol::kSecretSize];
  WiFiClient client_;
  HTTPClient http_;
  uint32_t offlineSince_ = 0;
  uint32_t lastJoinAttempt_ = 0;
  bool txPowerSet_ = false;
  int shownColor_ = -1;
  int shownStatus_ = -1;
};
