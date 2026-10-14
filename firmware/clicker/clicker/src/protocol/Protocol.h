// The clicker <-> Utz'tutor wire format (docs/api/devices.md, sessions.md, presence.md).
//
// Four calls, all JSON. The clicker speaks the same API as the phones:
//   POST /api/v1/devices/auth         its secret in, a token for its student out
//   GET  /api/v1/session/current      every second: "is a question open?" (public)
//   POST /api/v1/session/{id}/vote    when a button is pressed during an open question
//   POST /api/v1/presence/heartbeat   every 5 s: "still here", with signal and battery
// The vote and the heartbeat carry the token as "Authorization: Bearer <token>".
// Builders: RequestBodies.cpp. Parsers: ReplyParsers.cpp. What a status code means:
// ReplyMeaning.h. No Arduino calls in here, so it is unit-tested on a PC (hosttest/).
#pragma once

#include <stddef.h>
#include <stdint.h>

#include "../support/FixedText.h"

namespace protocol
{

  extern const char kLoginPath[];
  extern const char kSessionPath[];
  extern const char kHeartbeatPath[];

  const size_t kSecretSize = 33; // 32 lowercase hex characters
  const size_t kTokenSize = 65;  // the token is a 36-character UUID today
  const size_t kUsernameSize = 33;
  const size_t kSessionIdSize = 49; // "s_" + 12 hex characters today
  const size_t kRoundIdSize = 65;   // the session id + "_r" + the round number
  const size_t kPathSize = 96;
  const size_t kBodySize = 192;
  const size_t kDetailSize = 96;

  typedef FixedText<kTokenSize> Token;
  typedef FixedText<kSessionIdSize> SessionId;
  typedef FixedText<kRoundIdSize> RoundId;
  typedef FixedText<kDetailSize> ErrorDetail;

  // What the clicker keeps from a successful login.
  struct LoginReply
  {
    Token token;
    FixedText<kUsernameSize> username; // for the log only
  };

  // What the clicker needs from GET /session/current. The reply also carries the
  // question text and, after the reveal, the results: the clicker skips all of that.
  struct SessionView
  {
    bool roundOpen;
    SessionId sessionId;
    RoundId roundId; // "" when the match has no round yet
  };

  // ---- request bodies (each returns the length written) ----
  // {"device_id":"ESP32-A4CF12","secret":"3f9c..."}
  size_t loginBody(char *out, size_t cap, const char *deviceId, const char *secret);
  // {"rssi":-55,"battery_pct":88}. rssi outside -120..-1 and batteryPct outside 0..100
  // mean "unknown" and are left out.
  size_t heartbeatBody(char *out, size_t cap, int rssi, int batteryPct);
  // {"selected_option":"B","response_time_ms":1200}
  size_t voteBody(char *out, size_t cap, char option, uint32_t responseMs);
  // /api/v1/session/<sessionId>/vote
  size_t votePath(char *out, size_t cap, const char *sessionId);

  // ---- replies (each returns false when the JSON is not what the Utz'tutor sends) ----
  // A token that does not fit is refused whole, never cut.
  bool parseLogin(const char *json, LoginReply &reply);
  bool parseSession(const char *json, SessionView &view);
  // The "detail" message of an error reply, for the serial log. "" when there is none.
  ErrorDetail detailOf(const char *json);
  // True when a 409 on the vote means "this student already voted in this round", as
  // opposed to "the round is closed".
  bool isAlreadyVoted(const char *detail);

} // namespace protocol
