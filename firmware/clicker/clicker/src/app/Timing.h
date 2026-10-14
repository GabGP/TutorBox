// How often the clicker talks to the Utz'tutor, by situation. All in milliseconds.
#pragma once

#include <stdint.h>

namespace timing
{

  const uint32_t kPollEveryMs = 1000;       // "is a question open?"
  const uint32_t kHeartbeatEveryMs = 5000;  // "still here" for the teacher's lobby
  const uint32_t kRetryEveryMs = 2000;      // a login or a poll that got no answer
  const uint32_t kUnassignedEveryMs = 5000; // waiting for the teacher to assign it
  const uint32_t kLockedOutEveryMs = 30000; // after a 429 lockout
  const uint32_t kRefreshAfterVoteMs = 300; // re-read the round soon after a vote
  const uint8_t kFailuresBeforeUnreachable = 3;
  const uint8_t kVoteAttempts = 3;   // tries per vote when nothing answers
  const uint32_t kVoteRetryMs = 250; // between two tries of the same vote

} // namespace timing
