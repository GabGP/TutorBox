#include "Protocol.h"

#include <ArduinoJson.h>
#include <stdio.h>
#include <string.h>

namespace protocol {

const char kAuthPath[] = "/api/v1/devices/auth";
const char kSessionPath[] = "/api/v1/session/current";
const char kHeartbeatPath[] = "/api/v1/presence/heartbeat";

namespace {

void copyText(char* out, size_t cap, const char* text) {
  if (cap == 0) return;
  strncpy(out, text, cap - 1);
  out[cap - 1] = '\0';
}

// Like copyText, but refuses a text that does not fit instead of cutting it: half a
// token or half a session id is worse than none.
bool copyWhole(char* out, size_t cap, const char* text) {
  if (text == nullptr || text[0] == '\0' || strlen(text) >= cap) return false;
  copyText(out, cap, text);
  return true;
}

}  // namespace

bool isSecret(const char* text) {
  if (text == nullptr || strlen(text) != kSecretSize - 1) return false;
  for (size_t i = 0; i < kSecretSize - 1; i++) {
    const char c = text[i];
    const bool hex = (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f');
    if (!hex) return false;
  }
  return true;
}

int batteryPercent(int mv, int emptyMv, int fullMv) {
  if (mv < 0 || fullMv <= emptyMv) return -1;
  if (mv <= emptyMv) return 0;
  if (mv >= fullMv) return 100;
  return static_cast<int>((static_cast<long>(mv - emptyMv) * 100) / (fullMv - emptyMv));
}

size_t authBody(char* out, size_t cap, const char* deviceId, const char* secret) {
  JsonDocument doc;
  doc["device_id"] = deviceId;
  doc["secret"] = secret;
  return serializeJson(doc, out, cap);
}

size_t heartbeatBody(char* out, size_t cap, int rssi, int batteryPct) {
  JsonDocument doc;
  doc.to<JsonObject>();  // "{}" when both are unknown
  if (rssi < 0 && rssi >= -120) doc["rssi"] = rssi;
  if (batteryPct >= 0 && batteryPct <= 100) doc["battery_pct"] = batteryPct;
  return serializeJson(doc, out, cap);
}

size_t voteBody(char* out, size_t cap, char option, uint32_t responseMs) {
  const char selected[2] = {option, '\0'};
  JsonDocument doc;
  doc["selected_option"] = selected;
  doc["response_time_ms"] = responseMs;
  return serializeJson(doc, out, cap);
}

size_t votePath(char* out, size_t cap, const char* sessionId) {
  const int written = snprintf(out, cap, "/api/v1/session/%s/vote", sessionId);
  return written < 0 ? 0 : static_cast<size_t>(written);
}

bool parseAuth(const char* json, char* token, size_t tokenCap, char* username,
               size_t usernameCap) {
  JsonDocument doc;
  if (deserializeJson(doc, json)) return false;
  if (!copyWhole(token, tokenCap, doc["session_id"] | "")) return false;
  copyText(username, usernameCap, doc["username"] | "");
  return true;
}

bool parseSession(const char* json, SessionView& view) {
  JsonDocument wanted;
  wanted["id"] = true;
  wanted["current_round"]["round_id"] = true;
  wanted["current_round"]["status"] = true;
  JsonDocument doc;
  if (deserializeJson(doc, json, DeserializationOption::Filter(wanted))) return false;
  if (!copyWhole(view.sessionId, sizeof(view.sessionId), doc["id"] | "")) return false;
  const char* roundId = doc["current_round"]["round_id"] | "";
  const char* status = doc["current_round"]["status"] | "";
  view.roundId[0] = '\0';
  view.roundOpen = false;
  if (roundId[0] != '\0' && !copyWhole(view.roundId, sizeof(view.roundId), roundId)) {
    return false;
  }
  view.roundOpen = view.roundId[0] != '\0' && strcmp(status, "open") == 0;
  return true;
}

bool parseDetail(const char* json, char* out, size_t cap) {
  JsonDocument doc;
  if (deserializeJson(doc, json)) return false;
  if (!doc["detail"].is<const char*>()) return false;
  copyText(out, cap, doc["detail"].as<const char*>());
  return true;
}

bool isAlreadyVoted(const char* detail) {
  return detail != nullptr && strstr(detail, "already voted") != nullptr;
}

}  // namespace protocol
