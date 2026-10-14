// PC stand-in for the Arduino-ESP32 WiFi library (signatures as in 2.0.17 / 3.3.x).
// The simulator flips Wi-Fi on and off from its command line.
#pragma once

#include <functional>

#include "Arduino.h"

typedef enum
{
  WIFI_MODE_NULL = 0,
  WIFI_STA = 1
} wifi_mode_t;
typedef enum
{
  WL_IDLE_STATUS = 0,
  WL_CONNECTED = 3,
  WL_DISCONNECTED = 6
} wl_status_t;
typedef enum
{
  WIFI_POWER_19_5dBm = 78,
  WIFI_POWER_8_5dBm = 34
} wifi_power_t;

typedef enum
{
  WIFI_REASON_4WAY_HANDSHAKE_TIMEOUT = 15,
  WIFI_REASON_NO_AP_FOUND = 201,
  WIFI_REASON_AUTH_FAIL = 202,
  WIFI_REASON_HANDSHAKE_TIMEOUT = 204,
} wifi_err_reason_t;

typedef enum
{
  ARDUINO_EVENT_WIFI_STA_DISCONNECTED = 5,
  ARDUINO_EVENT_WIFI_STA_GOT_IP = 7,
  ARDUINO_EVENT_MAX = 100,
} arduino_event_id_t;

typedef struct
{
  uint8_t reason;
} wifi_event_sta_disconnected_t;

typedef union
{
  wifi_event_sta_disconnected_t wifi_sta_disconnected;
} arduino_event_info_t;

typedef arduino_event_id_t WiFiEvent_t;
typedef arduino_event_info_t WiFiEventInfo_t;
typedef std::function<void(arduino_event_id_t event, arduino_event_info_t info)>
    WiFiEventFuncCb;

class IPAddress
{
public:
  String toString() const { return String("127.0.0.1"); }
};

class WiFiClient
{
};

class WiFiClass
{
public:
  void persistent(bool persistent);
  static bool setHostname(const char *hostname);
  bool mode(wifi_mode_t mode);
  bool setAutoReconnect(bool autoReconnect);
  bool setSleep(bool enabled);
  int onEvent(WiFiEventFuncCb cbEvent, arduino_event_id_t event = ARDUINO_EVENT_MAX);
  wl_status_t begin(const char *ssid, const char *passphrase = NULL,
                    int32_t channel = 0, const uint8_t *bssid = NULL,
                    bool connect = true);
  bool setTxPower(wifi_power_t power);
  bool disconnect(bool wifioff = false, bool eraseap = false);
  wl_status_t status();
  int8_t RSSI();
  IPAddress localIP();
  const char *disconnectReasonName(wifi_err_reason_t reason);
};
extern WiFiClass WiFi;

// Simulator controls.
void simSetWifi(bool up);
