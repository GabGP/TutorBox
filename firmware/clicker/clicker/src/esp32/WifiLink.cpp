#include "WifiLink.h"

#include <Arduino.h>
#include <WiFi.h>

#include "../../config.h"

namespace
{

  const uint32_t kRejoinAfterMs = 20000UL;
  const uint32_t kRestartAfterMs = 180000UL;

  // Prints why Wi-Fi went down, with a hint for the two mistakes people make.
  void onWifiEvent(WiFiEvent_t event, WiFiEventInfo_t info)
  {
    if (event == ARDUINO_EVENT_WIFI_STA_GOT_IP)
    {
      Serial.printf("[wifi] connected: IP %s, signal %d dBm\n",
                    WiFi.localIP().toString().c_str(), WiFi.RSSI());
      return;
    }
    if (event != ARDUINO_EVENT_WIFI_STA_DISCONNECTED)
      return;
    const uint8_t reason = info.wifi_sta_disconnected.reason;
    Serial.printf("[wifi] not connected, reason %u (%s)\n", reason,
                  WiFi.disconnectReasonName(static_cast<wifi_err_reason_t>(reason)));
    if (reason == WIFI_REASON_NO_AP_FOUND)
    {
      Serial.println("[wifi] hint: is the router on? Is WIFI_SSID in secrets.h exact?");
    }
    else if (reason == WIFI_REASON_AUTH_FAIL ||
             reason == WIFI_REASON_4WAY_HANDSHAKE_TIMEOUT ||
             reason == WIFI_REASON_HANDSHAKE_TIMEOUT)
    {
      Serial.println("[wifi] hint: check WIFI_PASSWORD in secrets.h");
    }
  }

  // Many ESP32-C3 Super Mini boards lose Wi-Fi at full power (config.h, WIFI_LOW_TX_POWER).
  bool lowerTxPower()
  {
#if WIFI_LOW_TX_POWER
    return WiFi.setTxPower(WIFI_POWER_8_5dBm);
#else
    return true;
#endif
  }

} // namespace

void WifiLink::start(const char *hostname)
{
  WiFi.persistent(false);     // do not rewrite the password to flash on every boot
  WiFi.setHostname(hostname); // before mode(): the router lists "clicker-a4cf12"
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.setSleep(WIFI_POWER_SAVE != 0);
  WiFi.onEvent(onWifiEvent);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  txPowerSet_ = lowerTxPower();
  offlineSinceMs_ = millis();
  lastJoinAttemptMs_ = offlineSinceMs_;
}

void WifiLink::maintain(uint32_t nowMs)
{
  // Some cores refuse the power setting until the radio is fully up: try until it takes.
  if (!txPowerSet_)
    txPowerSet_ = lowerTxPower();
  if (connected())
  {
    offlineSinceMs_ = nowMs;
    return;
  }
  if (nowMs - offlineSinceMs_ > kRestartAfterMs)
  {
    Serial.println("[wifi] offline for 3 minutes: restarting the clicker");
    delay(100);
    ESP.restart();
  }
  if (nowMs - lastJoinAttemptMs_ > kRejoinAfterMs)
  {
    lastJoinAttemptMs_ = nowMs;
    Serial.println("[wifi] still offline, joining again");
    WiFi.disconnect();
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  }
}

bool WifiLink::connected() const { return WiFi.status() == WL_CONNECTED; }

int WifiLink::rssi() const { return WiFi.RSSI(); }
