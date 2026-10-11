// The clicker <-> TutorBox wire format (docs/api/clicker.md).
//
// Two calls, both POST with JSON and the X-Clicker-Id / X-Clicker-Secret headers:
//   /api/v1/clicker/checkin  every second: "here I am, is a question open?"
//   /api/v1/clicker/vote     when a button is pressed during an open question
// No Arduino calls in here, so it is unit-tested on a PC (hosttest/).
#pragma once

#include <stddef.h>
#include <stdint.h>

namespace protocol {

extern const char kCheckinPath[];
extern const char kVotePath[];

const size_t kRoundIdSize = 65;  // round ids are at most 64 characters

struct CheckinReply {
  bool assigned;
  bool roundOpen;
  bool voted;
  char roundId[kRoundIdSize];  // "" when no match is running
};

// Builds {"firmware":"1.0.0","rssi":-55,"battery_mv":3950}. rssi >= 0 and
// batteryMv < 0 mean "unknown" and are left out. Returns the length written.
size_t checkinBody(char* out, size_t cap, const char* firmware, int rssi,
                   int batteryMv);

// Builds {"round_id":"s_..._r0","selected_option":"B","response_time_ms":1200}.
size_t voteBody(char* out, size_t cap, const char* roundId, char option,
                uint32_t responseMs);

// Parses a check-in reply. False if it is not the JSON the TutorBox sends.
bool parseCheckin(const char* json, CheckinReply& reply);

// Copies the "detail" message of an error reply, for the serial log. False if none.
bool parseDetail(const char* json, char* out, size_t cap);

}  // namespace protocol
