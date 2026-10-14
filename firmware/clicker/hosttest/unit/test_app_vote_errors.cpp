// ClickerApp: a vote that is refused, retried, cut off by Wi-Fi or by the session.
#include <string.h>

#include "app_fixture.h"
#include "check.h"

void test_app_vote_errors()
{
  printf("ClickerApp: 409, retries, lost Wi-Fi, session ended mid-vote\n");
  gLog.clear();
  ClickerApp app;
  login(app, 0);
  Request req;
  CHECK(poll(app, 1000, 200, session("s_b", "s_b_r0", "open")));

  // 409 on the first attempt (voted on the phone, or time is up): red, round done.
  app.onButton('A', 1100);
  CHECK(app.nextRequest(1100, req) && req.kind == Kind::Vote);
  app.onResponse(req.kind, 409,
                 "{\"detail\":\"Student 4 has already voted in round s_b_r0.\"}", 1120);
  CHECK(logged("Vote A not accepted (Student 4 has already voted"));
  CHECK(app.ledColor(1120) == StatusLed::Red);
  CHECK(!app.armed());

  // Network hiccup, then "already voted" on the retry: the first try did arrive.
  CHECK(poll(app, 2000, 200, session("s_b", "s_b_r1", "open")));
  app.onButton('B', 2100);
  CHECK(app.nextRequest(2100, req));
  app.onResponse(req.kind, -11, "", 2200); // read timeout
  CHECK(logged("Vote B: no answer (-11), retrying"));
  CHECK(!app.nextRequest(2300, req)); // waits 250 ms, nothing else meanwhile
  CHECK(app.nextRequest(2450, req) && req.kind == Kind::Vote);
  app.onResponse(req.kind, 409,
                 "{\"detail\":\"Student 4 has already voted in round s_b_r1.\"}", 2460);
  CHECK(logged("Vote B counted (confirmed on retry)"));
  CHECK(app.ledColor(2460) == StatusLed::Green);

  // Hiccup, then "round closed" on the retry: that confirms nothing, so no green.
  CHECK(poll(app, 4000, 200, session("s_b", "s_b_r2", "open")));
  app.onButton('D', 4100);
  CHECK(app.nextRequest(4100, req));
  app.onResponse(req.kind, -11, "", 4200);
  CHECK(app.nextRequest(4450, req) && req.kind == Kind::Vote);
  app.onResponse(req.kind, 409, "{\"detail\":\"Round 's_b_r2' is not open.\"}", 4460);
  CHECK(logged("Vote D not accepted (Round 's_b_r2' is not open.)"));
  CHECK(app.ledColor(4460) == StatusLed::Red);
  CHECK(!app.armed());

  // Three failures in a row: red, and the student may press again.
  CHECK(poll(app, 6000, 200, session("s_b", "s_b_r3", "open")));
  app.onButton('C', 6100);
  uint32_t t = 6100;
  for (int i = 0; i < 3; i++)
  {
    CHECK(app.nextRequest(t, req) && req.kind == Kind::Vote);
    app.onResponse(req.kind, -1, "", t);
    t += 300;
  }
  CHECK(logged("Vote C failed (HTTP -1 ). Press again while the light is white."));
  CHECK(app.armed());

  // The match ended between the press and the vote: 404, round done.
  app.onButton('C', 7100);
  CHECK(app.nextRequest(7100, req) && req.kind == Kind::Vote);
  app.onResponse(req.kind, 404, "{\"detail\":\"Session not found.\"}", 7110);
  CHECK(logged("Vote C not accepted (Session not found.)"));
  CHECK(!app.armed());

  // Wi-Fi drops with a vote waiting: it is cancelled, never sent late.
  CHECK(poll(app, 8000, 200, session("s_b", "s_b_r4", "open")));
  app.onButton('D', 8100);
  app.setWifi(false, 8101);
  CHECK(logged("Vote D was NOT sent (no Wi-Fi)"));
  CHECK(app.phase() == Phase::LookingForWifi);
  CHECK(!app.nextRequest(8102, req));
  CHECK(app.ledColor(8102) == StatusLed::Red);

  // Back online: the token is still there, so no new login, the heartbeat goes first.
  app.setWifi(true, 9000);
  CHECK(logged("Wi-Fi connected again"));
  CHECK(app.phase() == Phase::Ready && !app.armed()); // not armed on old news
  CHECK(answer(app, 9000, Kind::Heartbeat, 204, ""));
  CHECK(poll(app, 9000, 200, session("s_b", "s_b_r4", "open")));
  CHECK(app.armed());

  // The session ended under a vote (401): log in again, then send the same vote.
  app.onButton('A', 9100);
  CHECK(app.nextRequest(9100, req) && req.kind == Kind::Vote);
  app.onResponse(req.kind, 401, kSessionEnded, 9110);
  CHECK(logged("Vote A: the session ended, logging in again"));
  CHECK(app.phase() == Phase::Connecting);
  CHECK(answer(app, 9110, Kind::Login, 200, kLoggedIn));
  CHECK(app.nextRequest(9120, req) && req.kind == Kind::Vote);
  CHECK(strcmp(req.path, "/api/v1/session/s_b/vote") == 0);
  app.onResponse(req.kind, 200, "{}", 9130);
  CHECK(logged("Vote A counted"));

  // Same, but the teacher took the clicker away: the vote is dropped and shown.
  CHECK(poll(app, 11000, 200, session("s_b", "s_b_r5", "open")));
  app.onButton('B', 11100);
  CHECK(app.nextRequest(11100, req) && req.kind == Kind::Vote);
  app.onResponse(req.kind, 401, kSessionEnded, 11110);
  CHECK(answer(app, 11110, Kind::Login, 403, kUnassigned));
  CHECK(logged("Vote B was NOT sent (no session)"));
  CHECK(app.phase() == Phase::Unassigned);
  CHECK(app.ledColor(11110) == StatusLed::Magenta);
  CHECK(!app.nextRequest(11120, req)); // no vote, and the next login is 5 s away

  // A 401 on the last try: the vote is dropped (red), and the clicker logs in again.
  ClickerApp lastTry;
  login(lastTry, 0);
  CHECK(poll(lastTry, 1000, 200, session("s_e", "s_e_r0", "open")));
  lastTry.onButton('A', 1100);
  CHECK(lastTry.nextRequest(1100, req));
  lastTry.onResponse(req.kind, -1, "", 1100);
  CHECK(lastTry.nextRequest(1350, req));
  lastTry.onResponse(req.kind, -1, "", 1350);
  CHECK(lastTry.nextRequest(1600, req) && req.kind == Kind::Vote);
  lastTry.onResponse(req.kind, 401, kSessionEnded, 1600);
  CHECK(lastTry.ledColor(1600) == StatusLed::Red);
  CHECK(lastTry.nextRequest(1600, req) && req.kind == Kind::Login);
  lastTry.onResponse(req.kind, 200, kLoggedIn, 1600);
  CHECK(lastTry.nextRequest(1600, req) && req.kind == Kind::Heartbeat); // no vote left
}
