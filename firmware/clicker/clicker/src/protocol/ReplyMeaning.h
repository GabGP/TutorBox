// What each HTTP status from the Utz'tutor means, per call. This is the only place
// that knows status codes; the app reads these outcomes and decides what to do.
// `status` is the HTTP status, or a negative number when the server did not answer.
#pragma once

#include <stdint.h>

namespace protocol
{

  enum class LoginOutcome : uint8_t
  {
    Accepted,      // 200 and a token
    Unassigned,    // 403: the teacher has not given it to a student (or just enrolled it)
    Refused,       // 401 or 422: the secret is not this clicker's, or malformed
    LockedOut,     // 429: too many refused logins
    NoLoginRoute,  // 404: a backend without the clicker login
    NotUnderstood, // 200, but not the JSON the Utz'tutor sends
    Failed         // no answer, or any other status
  };
  LoginOutcome loginOutcome(int status, bool replyUnderstood);
  // The teacher can fix it on /maestro/; waiting or retrying cannot.
  bool needsTeacher(LoginOutcome outcome);

  enum class PollOutcome : uint8_t
  {
    MatchRunning,  // 200 and a session
    NoMatch,       // 404: no match is running, which is normal
    NotUnderstood, // 200, but not the JSON the Utz'tutor sends
    Failed         // no answer, or any other status
  };
  PollOutcome pollOutcome(int status, bool replyUnderstood);

  enum class HeartbeatOutcome : uint8_t
  {
    Delivered,    // 2xx
    SessionEnded, // 401: unassigned, reassigned, deleted, a new secret, or 12 hours old
    Refused,      // any other 4xx
    NoAnswer      // no answer or 5xx: the poll, sent five times as often, reports that
  };
  HeartbeatOutcome heartbeatOutcome(int status);

  enum class VoteOutcome : uint8_t
  {
    Counted,        // 200
    CountedOnRetry, // 409 "already voted" on a retry: the first try did arrive
    NotAccepted,    // any other 409, or 404: the round closed or the match ended
    SessionEnded,   // 401: log in again
    RetrySoon,      // no answer or 5xx, with tries left
    Failed          // anything else, or out of tries
  };
  // `attemptsSoFar` counts the try this reply answers; `detail` is the reply's message.
  VoteOutcome voteOutcome(int status, uint8_t attemptsSoFar, uint8_t maxAttempts,
                          const char *detail);

} // namespace protocol
