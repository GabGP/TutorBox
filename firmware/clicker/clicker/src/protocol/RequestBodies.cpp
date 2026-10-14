// Builds the JSON bodies and paths the clicker sends (Protocol.h).
#include <ArduinoJson.h>
#include <stdio.h>

#include "Protocol.h"

namespace protocol
{

  const char kLoginPath[] = "/api/v1/devices/auth";
  const char kSessionPath[] = "/api/v1/session/current";
  const char kHeartbeatPath[] = "/api/v1/presence/heartbeat";

  namespace
  {
    const int kWeakestRssi = -120;
    const int kMaxBatteryPct = 100;
  } // namespace

  size_t loginBody(char *out, size_t cap, const char *deviceId, const char *secret)
  {
    JsonDocument doc;
    doc["device_id"] = deviceId;
    doc["secret"] = secret;
    return serializeJson(doc, out, cap);
  }

  size_t heartbeatBody(char *out, size_t cap, int rssi, int batteryPct)
  {
    JsonDocument doc;
    doc.to<JsonObject>(); // "{}" when both are unknown
    const bool rssiKnown = rssi < 0 && rssi >= kWeakestRssi;
    const bool batteryKnown = batteryPct >= 0 && batteryPct <= kMaxBatteryPct;
    if (rssiKnown)
      doc["rssi"] = rssi;
    if (batteryKnown)
      doc["battery_pct"] = batteryPct;
    return serializeJson(doc, out, cap);
  }

  size_t voteBody(char *out, size_t cap, char option, uint32_t responseMs)
  {
    const char selected[2] = {option, '\0'};
    JsonDocument doc;
    doc["selected_option"] = selected;
    doc["response_time_ms"] = responseMs;
    return serializeJson(doc, out, cap);
  }

  size_t votePath(char *out, size_t cap, const char *sessionId)
  {
    const int written = snprintf(out, cap, "/api/v1/session/%s/vote", sessionId);
    return written < 0 ? 0 : static_cast<size_t>(written);
  }

} // namespace protocol
