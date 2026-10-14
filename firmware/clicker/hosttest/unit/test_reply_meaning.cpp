// What each HTTP status means, per call (protocol/ReplyMeaning).
#include "check.h"
#include "src/protocol/ReplyMeaning.h"

using namespace protocol;

static void test_login_outcomes()
{
  printf("ReplyMeaning: login\n");
  CHECK(loginOutcome(200, true) == LoginOutcome::Accepted);
  CHECK(loginOutcome(200, false) == LoginOutcome::NotUnderstood);
  CHECK(loginOutcome(403, false) == LoginOutcome::Unassigned);
  CHECK(loginOutcome(401, false) == LoginOutcome::Refused);
  CHECK(loginOutcome(422, false) == LoginOutcome::Refused);
  CHECK(loginOutcome(429, false) == LoginOutcome::LockedOut);
  CHECK(loginOutcome(404, false) == LoginOutcome::NoLoginRoute);
  CHECK(loginOutcome(502, false) == LoginOutcome::Failed);
  CHECK(loginOutcome(-1, false) == LoginOutcome::Failed);
  CHECK(loginOutcome(400, false) == LoginOutcome::Failed);

  CHECK(needsTeacher(LoginOutcome::Unassigned));
  CHECK(needsTeacher(LoginOutcome::Refused));
  CHECK(needsTeacher(LoginOutcome::LockedOut));
  CHECK(!needsTeacher(LoginOutcome::Failed));
  CHECK(!needsTeacher(LoginOutcome::NoLoginRoute));
  CHECK(!needsTeacher(LoginOutcome::NotUnderstood));
}

static void test_poll_and_heartbeat_outcomes()
{
  printf("ReplyMeaning: poll, heartbeat\n");
  CHECK(pollOutcome(200, true) == PollOutcome::MatchRunning);
  CHECK(pollOutcome(200, false) == PollOutcome::NotUnderstood);
  CHECK(pollOutcome(404, false) == PollOutcome::NoMatch);
  CHECK(pollOutcome(500, false) == PollOutcome::Failed);
  CHECK(pollOutcome(-11, false) == PollOutcome::Failed);

  CHECK(heartbeatOutcome(204) == HeartbeatOutcome::Delivered);
  CHECK(heartbeatOutcome(401) == HeartbeatOutcome::SessionEnded);
  CHECK(heartbeatOutcome(403) == HeartbeatOutcome::Refused);
  CHECK(heartbeatOutcome(422) == HeartbeatOutcome::Refused);
  CHECK(heartbeatOutcome(499) == HeartbeatOutcome::Refused);
  CHECK(heartbeatOutcome(500) == HeartbeatOutcome::NoAnswer);
  CHECK(heartbeatOutcome(-1) == HeartbeatOutcome::NoAnswer);
}

static void test_vote_outcomes()
{
  printf("ReplyMeaning: vote\n");
  const char *already = "Student 4 has already voted in round s_x_r0.";
  const char *closed = "Round 's_x_r0' is not open.";
  CHECK(voteOutcome(200, 1, 3, "") == VoteOutcome::Counted);
  // "Already voted" proves the vote arrived only when this was a retry.
  CHECK(voteOutcome(409, 1, 3, already) == VoteOutcome::NotAccepted);
  CHECK(voteOutcome(409, 2, 3, already) == VoteOutcome::CountedOnRetry);
  CHECK(voteOutcome(409, 2, 3, closed) == VoteOutcome::NotAccepted);
  CHECK(voteOutcome(404, 2, 3, already) == VoteOutcome::NotAccepted);
  CHECK(voteOutcome(401, 1, 3, "") == VoteOutcome::SessionEnded);
  CHECK(voteOutcome(401, 3, 3, "") == VoteOutcome::SessionEnded);
  // No answer: tries left means try again, the last try means give up.
  CHECK(voteOutcome(-11, 1, 3, "") == VoteOutcome::RetrySoon);
  CHECK(voteOutcome(503, 2, 3, "") == VoteOutcome::RetrySoon);
  CHECK(voteOutcome(-1, 3, 3, "") == VoteOutcome::Failed);
  CHECK(voteOutcome(422, 1, 3, "") == VoteOutcome::Failed); // a refusal is not retried
}

void test_reply_meaning()
{
  test_login_outcomes();
  test_poll_and_heartbeat_outcomes();
  test_vote_outcomes();
}
