// One HTTP request the app wants sent. esp32/HttpLink.cpp sends it and hands the reply
// back to ClickerApp::onResponse, tagged with the same kind.
#pragma once

#include <stdint.h>

#include "../protocol/Protocol.h"

enum class RequestKind : uint8_t
{
  None,
  Login,
  Poll,
  Heartbeat,
  Vote
};

struct Request
{
  RequestKind kind;
  bool post;          // false: a GET with no body
  const char *bearer; // the token for the Authorization header, or nullptr
  char path[protocol::kPathSize];
  char body[protocol::kBodySize];
};

// Each fills `out` completely.
void makeLoginRequest(Request &out, const char *deviceId, const char *secret);
// A GET, public: the token is not sent where it is not needed.
void makePollRequest(Request &out);
void makeHeartbeatRequest(Request &out, const char *token, int rssi, int batteryPct);
void makeVoteRequest(Request &out, const char *token, const char *sessionId, char option,
                     uint32_t responseMs);
