#include "HttpLink.h"

#include "../../config.h"

namespace
{
  const uint16_t kConnectTimeoutMs = 1500;
  const uint16_t kReplyTimeoutMs = 2500;
  const int kNoContent = 204;
} // namespace

void HttpLink::begin() { http_.setReuse(true); }

int HttpLink::send(const Request &request, String &reply)
{
  reply = String();
  char url[160];
  snprintf(url, sizeof(url), "%s%s", UTZTUTOR_URL, request.path);
  http_.setConnectTimeout(kConnectTimeoutMs);
  http_.setTimeout(kReplyTimeoutMs);

  if (!http_.begin(client_, url))
    return HTTPC_ERROR_CONNECTION_REFUSED;

  if (request.bearer != nullptr)
  {
    char authorization[8 + protocol::kTokenSize];
    snprintf(authorization, sizeof(authorization), "Bearer %s", request.bearer);
    http_.addHeader("Authorization", authorization);
  }

  int status;
  if (request.post)
  {
    http_.addHeader("Content-Type", "application/json");
    status = http_.POST(reinterpret_cast<uint8_t *>(const_cast<char *>(request.body)),
                        strlen(request.body));
  }
  else
  {
    status = http_.GET();
  }

  // A 204 (the heartbeat's answer) has no body and no Content-Length. Asked for the
  // body anyway, HTTPClient reads until the server closes the connection we keep open:
  // about a minute with nginx, with no polls, heartbeats or votes meanwhile.
  if (status > 0 && status != kNoContent)
    reply = http_.getString();
  http_.end();
  return status;
}
