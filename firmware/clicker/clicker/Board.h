// Everything that touches the ESP32 hardware: pins, Wi-Fi, HTTP and flash storage.
// The decisions live in ClickerApp; this file only does what it is told.
#pragma once

#include <Arduino.h>
#include <HTTPClient.h>
#include <WiFi.h>

#include "Buttons.h"
#include "StatusLed.h"

class Board {
 public:
  // Pins, button interrupts, identity (device id + secret) and Wi-Fi start.
  void begin();

  const char* deviceId() const { return deviceId_; }

  bool wifiConnected() const;
  // Keeps Wi-Fi alive: re-joins after 20 s offline, restarts after 3 minutes.
  void maintainWifi(uint32_t nowMs);
  int rssi() const;
  int batteryMv() const;

  void readButtons(bool pressed[ButtonBank::kCount],
                   uint32_t edges[ButtonBank::kCount]) const;

  // POSTs JSON to TUTORBOX_URL + path with the clicker headers. Returns the HTTP
  // status, or a negative HTTPClient error when the server could not be reached.
  int post(const char* path, const char* body, char* reply, size_t replySize);

  void showColor(StatusLed::Color color);
  void showStatus(bool on);

 private:
  void loadOrCreateSecret();
  void startWifi();

  char deviceId_[16];
  char hostname_[24];
  char secret_[33];
  WiFiClient client_;
  HTTPClient http_;
  uint32_t offlineSince_ = 0;
  uint32_t lastJoinAttempt_ = 0;
  bool txPowerSet_ = false;
  int shownColor_ = -1;
  int shownStatus_ = -1;
};
