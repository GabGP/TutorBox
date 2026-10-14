// ClickerApp: an open question, a vote, a second press, and the round moving on.
#include <string.h>

#include "app_fixture.h"
#include "check.h"

void test_app_voting()
{
  printf("ClickerApp: open question, vote, second press\n");
  gLog.clear();
  ClickerApp app;
  login(app, 0);
  Request req;

  app.onButton('B', 50); // no question yet: red x3 (until 950 ms)
  CHECK(app.ledColor(50) == StatusLed::Red);
  CHECK(logged("no question is open"));

  // The lobby: a match exists but its first question is not open.
  CHECK(poll(app, 1000, 200, session("s_a", "s_a_r0", "pending")));
  CHECK(!app.armed());

  CHECK(poll(app, 2000, 200, session("s_a", "s_a_r0", "open")));
  CHECK(app.armed());
  CHECK(logged("Question open (s_a_r0)"));
  CHECK(app.ledColor(2000) == StatusLed::White);
  CHECK(app.ledColor(2750) == StatusLed::Off);

  app.onButton('C', 3200);
  CHECK(logged("Button C: sending vote for s_a_r0"));
  CHECK(app.ledColor(3200) == StatusLed::Yellow);
  CHECK(app.nextRequest(3200, req));
  CHECK(req.kind == Kind::Vote && req.post);
  CHECK(strcmp(req.path, "/api/v1/session/s_a/vote") == 0);
  CHECK(req.bearer != nullptr && strcmp(req.bearer, kToken) == 0);
  // The response time counts from when the clicker first saw the question open.
  CHECK(strcmp(req.body, "{\"selected_option\":\"C\",\"response_time_ms\":1200}") == 0);
  app.onButton('D', 3210);            // while sending: ignored
  CHECK(!app.nextRequest(3220, req)); // nothing else while the vote is in flight

  app.onResponse(Kind::Vote, 200, "{}", 3230);
  CHECK(logged("Vote C counted"));
  CHECK(app.ledColor(3230) == StatusLed::Green);
  CHECK(app.ledColor(4700) == StatusLed::Green);               // 1.5 s of green
  CHECK(!app.armed());                                         // answered: this round is done
  CHECK(!app.nextRequest(3529, req));                          // the round is read again soon...
  CHECK(app.nextRequest(3530, req) && req.kind == Kind::Poll); // ...300 ms later
  app.onResponse(req.kind, 200, session("s_a", "s_a_r0", "open").c_str(), 3530);

  app.onButton('A', 4800); // second press in the same round
  CHECK(logged("already answered"));
  CHECK(app.ledColor(4800) == StatusLed::Red);
  CHECK(poll(app, 4800, 200, session("s_a", "s_a_r0", "open")));
  CHECK(!app.armed()); // the round is still open on the server: still done for us

  CHECK(poll(app, 6000, 200, session("s_a", "s_a_r0", "revealed")));
  CHECK(!app.armed());
  CHECK(poll(app, 7000, 200, session("s_a", "s_a_r1", "open"))); // next question
  CHECK(app.armed());
  CHECK(poll(app, 8000, 200, session("s_a", "s_a_r1", "closed"))); // time is up
  CHECK(!app.armed());
  CHECK(poll(app, 9000, 404, kNoSession)); // the match ended
  CHECK(!app.armed() && app.phase() == Phase::Ready);
}
