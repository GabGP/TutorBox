#include "Request.h"

#include <stdio.h>

namespace
{
  void start(Request &out, RequestKind kind, bool post, const char *bearer)
  {
    out.kind = kind;
    out.post = post;
    out.bearer = bearer;
    out.path[0] = '\0';
    out.body[0] = '\0';
  }

  void setPath(Request &out, const char *path)
  {
    snprintf(out.path, sizeof(out.path), "%s", path);
  }
} // namespace

void makeLoginRequest(Request &out, const char *deviceId, const char *secret)
{
  start(out, RequestKind::Login, true, nullptr);
  setPath(out, protocol::kLoginPath);
  protocol::loginBody(out.body, sizeof(out.body), deviceId, secret);
}

void makePollRequest(Request &out)
{
  start(out, RequestKind::Poll, false, nullptr);
  setPath(out, protocol::kSessionPath);
}

void makeHeartbeatRequest(Request &out, const char *token, int rssi, int batteryPct)
{
  start(out, RequestKind::Heartbeat, true, token);
  setPath(out, protocol::kHeartbeatPath);
  protocol::heartbeatBody(out.body, sizeof(out.body), rssi, batteryPct);
}

void makeVoteRequest(Request &out, const char *token, const char *sessionId, char option,
                     uint32_t responseMs)
{
  start(out, RequestKind::Vote, true, token);
  protocol::votePath(out.path, sizeof(out.path), sessionId);
  protocol::voteBody(out.body, sizeof(out.body), option, responseMs);
}
