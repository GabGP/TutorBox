// The app's small parts on their own: RoundTracker, PendingVote and the requests.
// ClickerApp's scenarios (test_app_*.cpp) cover how they work together.
#include <string.h>

#include "check.h"
#include "src/app/PendingVote.h"
#include "src/app/Request.h"
#include "src/app/RoundTracker.h"

static protocol::SessionView view(const char *sessionId, const char *roundId, bool open)
{
  protocol::SessionView made;
  made.sessionId.assignTruncated(sessionId);
  made.roundId.assignTruncated(roundId);
  made.roundOpen = open;
  return made;
}

static void test_round_tracker()
{
  printf("RoundTracker\n");
  RoundTracker rounds;
  CHECK(!rounds.isOpen() && !rounds.waitingForAnswer());

  rounds.follow(view("s_a", "s_a_r0", true));
  CHECK(rounds.isOpen() && rounds.waitingForAnswer() && !rounds.noticed());
  CHECK(strcmp(rounds.sessionId(), "s_a") == 0 && strcmp(rounds.roundId(), "s_a_r0") == 0);
  rounds.notice(1000);
  CHECK(rounds.noticed() && rounds.msSinceNoticed(1250) == 250);
  rounds.follow(view("s_a", "s_a_r0", true)); // the same round again: still noticed
  CHECK(rounds.noticed());

  rounds.markAnswered("s_a_r0");
  CHECK(rounds.isOpen() && !rounds.waitingForAnswer()); // open, but done for us
  rounds.follow(view("s_a", "s_a_r1", true));           // the next question
  CHECK(rounds.waitingForAnswer() && !rounds.noticed());

  rounds.forgetOpenRound(); // Wi-Fi lost or session ended: closed until the next poll
  CHECK(!rounds.isOpen() && !rounds.waitingForAnswer());
  rounds.follow(view("s_a", "", true)); // a match with no round id: nothing to answer
  CHECK(!rounds.waitingForAnswer());
}

static void test_pending_vote()
{
  printf("PendingVote\n");
  PendingVote vote;
  CHECK(!vote.isPending() && !vote.tryIsDue(0));

  vote.start('C', "s_a", "s_a_r0", 1200, 5000);
  CHECK(vote.isPending() && vote.option() == 'C' && vote.responseMs() == 1200);
  CHECK(strcmp(vote.sessionId(), "s_a") == 0 && strcmp(vote.roundId(), "s_a_r0") == 0);
  CHECK(vote.tryIsDue(5000) && vote.attempts() == 0); // the first try goes at once
  vote.countTry();
  vote.retryIn(5000, 250);
  CHECK(!vote.tryIsDue(5249) && vote.tryIsDue(5250) && vote.attempts() == 1);

  vote.clear();
  CHECK(!vote.isPending() && !vote.tryIsDue(9000));
  CHECK(vote.option() == 'C'); // still readable for the log line after it ends

  vote.start('A', "s_b", "s_b_r0", 0, 9000); // a new vote starts its count again
  CHECK(vote.attempts() == 0 && strcmp(vote.sessionId(), "s_b") == 0);
}

static void test_requests()
{
  printf("Request\n");
  Request request;
  makeLoginRequest(request, "ESP32-T", "0123456789abcdef0123456789abcdef");
  CHECK(request.kind == RequestKind::Login && request.post && request.bearer == nullptr);
  CHECK(strcmp(request.path, "/api/v1/devices/auth") == 0);

  makePollRequest(request); // the body of the previous request is gone
  CHECK(request.kind == RequestKind::Poll && !request.post && request.bearer == nullptr);
  CHECK(strcmp(request.path, "/api/v1/session/current") == 0 && request.body[0] == '\0');

  const char *token = "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d";
  makeHeartbeatRequest(request, token, -60, 80);
  CHECK(request.kind == RequestKind::Heartbeat && request.post && request.bearer == token);
  CHECK(strcmp(request.body, "{\"rssi\":-60,\"battery_pct\":80}") == 0);

  makeVoteRequest(request, token, "s_a", 'D', 900);
  CHECK(request.kind == RequestKind::Vote && request.post && request.bearer == token);
  CHECK(strcmp(request.path, "/api/v1/session/s_a/vote") == 0);
  CHECK(strcmp(request.body, "{\"selected_option\":\"D\",\"response_time_ms\":900}") == 0);
}

void test_app_parts()
{
  test_round_tracker();
  test_pending_vote();
  test_requests();
}
