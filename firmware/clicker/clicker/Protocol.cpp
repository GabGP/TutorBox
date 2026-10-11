#include "Protocol.h"

#include <ArduinoJson.h>
#include <string.h>

namespace protocol {

const char kCheckinPath[] = "/api/v1/clicker/checkin";
const char kVotePath[] = "/api/v1/clicker/vote";

namespace {
void copyText(char* out, size_t cap, const char* text) {
  if (cap == 0) return;
  strncpy(out, text, cap - 1);
  out[cap - 1] = '\0';
}
}  // namespace

size_t checkinBody(char* out, size_t cap, const char* firmware, int rssi,
                   int batteryMv) {
  JsonDocument doc;
  doc["firmware"] = firmware;
  if (rssi < 0) doc["rssi"] = rssi;
  if (batteryMv >= 0) doc["battery_mv"] = batteryMv;
  return serializeJson(doc, out, cap);
}

size_t voteBody(char* out, size_t cap, const char* roundId, char option,
                uint32_t responseMs) {
  const char selected[2] = {option, '\0'};
  JsonDocument doc;
  doc["round_id"] = roundId;
  doc["selected_option"] = selected;
  doc["response_time_ms"] = responseMs;
  return serializeJson(doc, out, cap);
}

bool parseCheckin(const char* json, CheckinReply& reply) {
  JsonDocument doc;
  if (deserializeJson(doc, json)) return false;
  if (!doc["assigned"].is<bool>()) return false;
  reply.assigned = doc["assigned"].as<bool>();
  reply.roundOpen = doc["round_open"] | false;
  reply.voted = doc["voted"] | false;
  copyText(reply.roundId, sizeof(reply.roundId), doc["round_id"] | "");
  return true;
}

bool parseDetail(const char* json, char* out, size_t cap) {
  JsonDocument doc;
  if (deserializeJson(doc, json)) return false;
  if (!doc["detail"].is<const char*>()) return false;
  copyText(out, cap, doc["detail"].as<const char*>());
  return true;
}

}  // namespace protocol
