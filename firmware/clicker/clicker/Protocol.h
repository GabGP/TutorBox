// The clicker <-> Utz'tutor wire format (docs/api/devices.md, sessions.md, presence.md).
//
// Four calls, all JSON. The clicker speaks the same API as the phones:
//   POST /api/v1/devices/auth         its secret in, a token for its student out
//   GET  /api/v1/session/current      every second: "is a question open?" (public)
//   POST /api/v1/session/{id}/vote    when a button is pressed during an open question
//   POST /api/v1/presence/heartbeat   every 5 s: "still here", with signal and battery
// The vote and the heartbeat carry the token as "Authorization: Bearer <token>".
// No Arduino calls in here, so it is unit-tested on a PC (hosttest/).
#pragma once

#include <stddef.h>
#include <stdint.h>

namespace protocol {

extern const char kAuthPath[];
extern const char kSessionPath[];
extern const char kHeartbeatPath[];

const size_t kSecretSize = 33;     // 32 lowercase hex characters
const size_t kTokenSize = 65;      // the token is a 36-character UUID today
const size_t kUsernameSize = 33;
const size_t kSessionIdSize = 49;  // "s_" + 12 hex characters today
const size_t kRoundIdSize = 65;    // the session id + "_r" + the round number
const size_t kPathSize = 96;

// What the clicker needs from GET /session/current. The reply also carries the
// question text and, after the reveal, the results: the clicker skips all of that.
struct SessionView {
  bool roundOpen;
  char sessionId[kSessionIdSize];
  char roundId[kRoundIdSize];  // "" when the match has no round yet
};

// True for exactly 32 lowercase hex characters, the shape the clicker makes for itself.
bool isSecret(const char* text);

// Battery voltage as 0..100, straight line between empty and full. -1 if mv < 0.
int batteryPercent(int mv, int emptyMv, int fullMv);

// Builds {"device_id":"ESP32-A4CF12","secret":"3f9c..."}. Returns the length written.
size_t authBody(char* out, size_t cap, const char* deviceId, const char* secret);

// Builds {"rssi":-55,"battery_pct":88}. rssi outside -120..-1 and batteryPct outside
// 0..100 mean "unknown" and are left out.
size_t heartbeatBody(char* out, size_t cap, int rssi, int batteryPct);

// Builds {"selected_option":"B","response_time_ms":1200}.
size_t voteBody(char* out, size_t cap, char option, uint32_t responseMs);

// Builds /api/v1/session/<sessionId>/vote.
size_t votePath(char* out, size_t cap, const char* sessionId);

// Reads the token (and the student's username, for the log) from a login reply.
// False if the reply is not the JSON the Utz'tutor sends, or the token does not fit.
bool parseAuth(const char* json, char* token, size_t tokenCap, char* username,
               size_t usernameCap);

// Parses GET /session/current. False if it is not the JSON the Utz'tutor sends.
bool parseSession(const char* json, SessionView& view);

// Copies the "detail" message of an error reply, for the serial log. False if none.
bool parseDetail(const char* json, char* out, size_t cap);

// True when a 409 on the vote means "this student already voted in this round",
// as opposed to "the round is closed".
bool isAlreadyVoted(const char* detail);

}  // namespace protocol
