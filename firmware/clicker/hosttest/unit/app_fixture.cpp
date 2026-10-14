#include "app_fixture.h"

#include "check.h"

const char *const kSecret = "0123456789abcdef0123456789abcdef";
const char *const kToken = "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d";
const char *const kLoggedIn =
    "{\"session_id\":\"9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d\",\"username\":\"ana\","
    "\"device_id\":\"ESP32-T\"}";
const char *const kUnassigned = "{\"detail\":\"Device is not assigned to any student.\"}";
const char *const kRefused = "{\"detail\":\"Invalid device credentials.\"}";
const char *const kLockedOut =
    "{\"detail\":\"Too many failed login attempts. Please try again later.\"}";
const char *const kNoSession = "{\"detail\":\"No active session.\"}";
const char *const kSessionEnded = "{\"detail\":\"Invalid or expired session.\"}";

std::string session(const char *sessionId, const char *roundId, const char *status)
{
  std::string s = std::string("{\"id\":\"") + sessionId +
                  "\",\"title\":\"Repaso\",\"topic\":\"arithmetic\",\"status\":\"active\","
                  "\"current_round_index\":0,\"question_count\":3,\"current_round\":";
  if (roundId == nullptr)
    return s + "null}";
  s += std::string("{\"round_id\":\"") + roundId + "\",\"round_index\":0,\"status\":\"" +
       status +
       "\",\"question_id\":\"q_add_001\",\"duration_seconds\":20,"
       "\"time_remaining\":12.5,\"votes_cast\":7,\"question\":{\"question_text\":"
       "\"\\u00bfCu\\u00e1nto es 54 + 38?\",\"options\":{\"A\":\"82\",\"B\":\"16\","
       "\"C\":\"92\",\"D\":\"812\"}},\"result\":null}}";
  return s;
}

bool answer(ClickerApp &app, uint32_t nowMs, Kind kind, int status, const char *body)
{
  Request request;
  if (!app.nextRequest(nowMs, request) || request.kind != kind)
    return false;
  app.onResponse(request.kind, status, body, nowMs);
  return true;
}

bool poll(ClickerApp &app, uint32_t nowMs, int status, const std::string &body)
{
  Request request;
  if (!app.nextRequest(nowMs, request))
    return false;
  if (request.kind == Kind::Heartbeat)
  {
    app.onResponse(request.kind, 204, "", nowMs);
    if (!app.nextRequest(nowMs, request))
      return false;
  }
  if (request.kind != Kind::Poll)
    return false;
  app.onResponse(request.kind, status, body.c_str(), nowMs);
  return true;
}

void powerOn(ClickerApp &app, uint32_t nowMs)
{
  app.begin("ESP32-T", "2.1.0", kSecret, captureLog, nowMs);
  app.setWifi(true, nowMs);
}

void login(ClickerApp &app, uint32_t nowMs)
{
  powerOn(app, nowMs);
  CHECK(answer(app, nowMs, Kind::Login, 200, kLoggedIn));
  CHECK(answer(app, nowMs, Kind::Heartbeat, 204, ""));
  CHECK(answer(app, nowMs, Kind::Poll, 404, kNoSession));
  CHECK(app.phase() == Phase::Ready);
}
