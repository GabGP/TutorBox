// Reads the Utz'tutor's JSON replies (Protocol.h).
#include <ArduinoJson.h>
#include <string.h>

#include "Protocol.h"

namespace protocol
{

  bool parseLogin(const char *json, LoginReply &reply)
  {
    JsonDocument doc;
    if (deserializeJson(doc, json))
      return false;
    if (!reply.token.assignWhole(doc["session_id"] | ""))
      return false;
    reply.username.assignTruncated(doc["username"] | "");
    return true;
  }

  bool parseSession(const char *json, SessionView &view)
  {
    // Only these fields are kept: the question text and the results are skipped.
    JsonDocument wanted;
    wanted["id"] = true;
    wanted["current_round"]["round_id"] = true;
    wanted["current_round"]["status"] = true;
    JsonDocument doc;
    if (deserializeJson(doc, json, DeserializationOption::Filter(wanted)))
      return false;
    if (!view.sessionId.assignWhole(doc["id"] | ""))
      return false;

    const char *roundId = doc["current_round"]["round_id"] | "";
    const char *status = doc["current_round"]["status"] | "";
    view.roundId.wipe();
    view.roundOpen = false;
    const bool hasRound = roundId[0] != '\0';
    if (hasRound && !view.roundId.assignWhole(roundId))
      return false;
    view.roundOpen = hasRound && strcmp(status, "open") == 0;
    return true;
  }

  ErrorDetail detailOf(const char *json)
  {
    ErrorDetail detail;
    JsonDocument doc;
    if (deserializeJson(doc, json))
      return detail;
    // FastAPI's validation errors put a list here, not a message: those are left out.
    if (doc["detail"].is<const char *>())
    {
      detail.assignTruncated(doc["detail"].as<const char *>());
    }
    return detail;
  }

  bool isAlreadyVoted(const char *detail)
  {
    return detail != nullptr && strstr(detail, "already voted") != nullptr;
  }

} // namespace protocol
