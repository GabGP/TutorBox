// Stand-in for the WiFi library. The radio comes up 300 ms after begin(), and the test
// switches the access point off and on with "wifi off" / "wifi on" (sim_main.cpp).
#include <vector>

#include "WiFi.h"
#include "sim_state.h"

WiFiClass WiFi;

namespace
{

  bool gWifiWanted = true; // the simulated access point is reachable
  bool gWifiStarted = false;
  bool gWifiUp = false;
  unsigned long gWifiUpAt = 0;
  std::vector<WiFiEventFuncCb> gWifiHandlers;

  void notifyWifi(arduino_event_id_t event, uint8_t reason)
  {
    arduino_event_info_t info;
    info.wifi_sta_disconnected.reason = reason;
    for (size_t i = 0; i < gWifiHandlers.size(); i++)
      gWifiHandlers[i](event, info);
  }

  void updateWifi()
  {
    const bool up = gWifiStarted && gWifiWanted && millis() >= gWifiUpAt;
    if (up == gWifiUp)
      return;
    gWifiUp = up;
    notifyWifi(up ? ARDUINO_EVENT_WIFI_STA_GOT_IP : ARDUINO_EVENT_WIFI_STA_DISCONNECTED,
               up ? 0 : WIFI_REASON_NO_AP_FOUND);
  }

} // namespace

bool simWifiUp() { return gWifiUp; }

void simSetWifi(bool up)
{
  gWifiWanted = up;
  if (up)
    gWifiUpAt = millis() + 300;
}

void WiFiClass::persistent(bool persistent) { (void)persistent; }
bool WiFiClass::setHostname(const char *hostname)
{
  ::printf("SIM hostname %s\n", hostname);
  return true;
}
bool WiFiClass::mode(wifi_mode_t mode) { return mode == WIFI_STA; }
bool WiFiClass::setAutoReconnect(bool autoReconnect) { return autoReconnect; }
bool WiFiClass::setSleep(bool enabled)
{
  (void)enabled;
  return true;
}
int WiFiClass::onEvent(WiFiEventFuncCb cbEvent, arduino_event_id_t event)
{
  (void)event;
  gWifiHandlers.push_back(cbEvent);
  return static_cast<int>(gWifiHandlers.size());
}
wl_status_t WiFiClass::begin(const char *ssid, const char *passphrase, int32_t channel,
                             const uint8_t *bssid, bool connect)
{
  (void)ssid;
  (void)passphrase;
  (void)channel;
  (void)bssid;
  (void)connect;
  gWifiStarted = true;
  gWifiUpAt = millis() + 300; // association + DHCP take a moment
  return WL_DISCONNECTED;
}
bool WiFiClass::setTxPower(wifi_power_t power)
{
  ::printf("SIM tx power %d\n", static_cast<int>(power));
  return gWifiStarted;
}
bool WiFiClass::disconnect(bool wifioff, bool eraseap)
{
  (void)wifioff;
  (void)eraseap;
  return true;
}
wl_status_t WiFiClass::status()
{
  updateWifi();
  return gWifiUp ? WL_CONNECTED : WL_DISCONNECTED;
}
int8_t WiFiClass::RSSI() { return gWifiUp ? -58 : 0; }
IPAddress WiFiClass::localIP() { return IPAddress(); }
const char *WiFiClass::disconnectReasonName(wifi_err_reason_t reason)
{
  return reason == WIFI_REASON_NO_AP_FOUND ? "NO_AP_FOUND" : "UNSPECIFIED";
}
