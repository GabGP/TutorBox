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
  // Pins, button interrupts, identity (device id) and the start-up banner. The radio
  // and the secret come later, in the order of clicker.ino's setup().
  void begin();

  const char* deviceId() const { return deviceId_; }
  // The secret this clicker logs in with: 32 hex characters that it made itself
  // (loadOrCreateSecret). "" until loadOrCreateSecret() has run.
  const char* secret() const { return secret_; }

  // Starts the Wi-Fi radio. Call once, after begin() and the reset gesture check.
  void startWifi();
  // Reads the secret from flash, or makes one the first time (a restart keeps it).
  // Call after startWifi(): esp_random() is only truly random while the radio is on.
  void loadOrCreateSecret();
  // Erases the stored secret: the next loadOrCreateSecret() makes a new one. False if
  // flash refused the erase, and then the old secret is kept.
  bool resetSecret();

  bool wifiConnected() const;
  // Keeps Wi-Fi alive: re-joins after 20 s offline, restarts after 3 minutes.
  void maintainWifi(uint32_t nowMs);
  int rssi() const;
  // Battery as 0..100, or -1 when the two sense resistors are not fitted.
  int batteryPct() const;

  void readButtons(bool pressed[ButtonBank::kCount],
                   uint32_t edges[ButtonBank::kCount]) const;

  // Sends the request to TUTORBOX_URL + path. Returns the HTTP status, or a negative
  // HTTPClient error when the server could not be reached. `reply` gets the body.
  int send(const ClickerApp::Request& request, String& reply);

  void showColor(StatusLed::Color color);
  void showStatus(bool on);

 private:
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
