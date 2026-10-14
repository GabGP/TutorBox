// ClickerApp: the session ended by the teacher, and a Utz'tutor that stops answering.
#include "app_fixture.h"
#include "check.h"

static void test_session_ended()
{
  printf("ClickerApp: unassigned or reassigned while it runs\n");
  gLog.clear();
  ClickerApp app;
  login(app, 0);
  Request req;
  CHECK(poll(app, 1000, 200, session("s_c", "s_c_r0", "open")));
  CHECK(app.armed());

  // The heartbeat is what tells a clicker that the teacher took it away.
  CHECK(answer(app, 5000, Kind::Heartbeat, 401, kSessionEnded));
  CHECK(logged("Utz'tutor ended this clicker's session"));
  CHECK(app.phase() == Phase::Connecting && !app.armed());
  CHECK(answer(app, 5000, Kind::Login, 403, kUnassigned));
  CHECK(app.phase() == Phase::Unassigned);
  CHECK(!app.nextRequest(5001, req)); // no polls and no heartbeats without a token

  // Assigned to another student: a new token, voting again.
  CHECK(answer(app, 10000, Kind::Login, 200, kLoggedIn));
  CHECK(answer(app, 10000, Kind::Heartbeat, 204, ""));
  CHECK(poll(app, 10000, 200, session("s_c", "s_c_r0", "open")));
  CHECK(app.armed());

  // A heartbeat the server refuses for another reason is logged, nothing more.
  CHECK(answer(app, 15000, Kind::Heartbeat, 422, "{\"detail\":[{\"msg\":\"bad\"}]}"));
  CHECK(logged("Heartbeat refused (HTTP 422"));
  CHECK(app.phase() == Phase::Ready);
  // A heartbeat that got no answer is left to the poll to report.
  CHECK(poll(app, 15000, 200, session("s_c", "s_c_r0", "open")));
  CHECK(answer(app, 20000, Kind::Heartbeat, -1, ""));
  CHECK(app.phase() == Phase::Ready && app.armed());

  // A reply for no request at all changes nothing (and the next request may go).
  app.onResponse(Kind::None, 200, "{}", 20000);
  CHECK(app.phase() == Phase::Ready && app.armed());
}

static void test_server_problems()
{
  printf("ClickerApp: server down, the Utz'tutor answers again, logged in then silent\n");
  gLog.clear();
  ClickerApp app;
  powerOn(app, 0);
  Request req;

  CHECK(answer(app, 0, Kind::Login, -1, ""));
  CHECK(logged("Login failed (-1 )"));
  CHECK(app.phase() == Phase::Connecting);
  CHECK(!app.nextRequest(1500, req)); // retries every 2 s
  CHECK(answer(app, 2000, Kind::Login, 502, "bad gateway"));
  CHECK(answer(app, 4000, Kind::Login, -1, ""));
  CHECK(app.phase() == Phase::ServerUnreachable);
  CHECK(app.ledColor(4000) == StatusLed::Blue && app.ledColor(5100) == StatusLed::Off);
  app.onButton('A', 5200);
  CHECK(logged("not connected yet"));
  CHECK(app.ledColor(5200) == StatusLed::Red);

  CHECK(answer(app, 6000, Kind::Login, 404, "{\"detail\":\"Not Found\"}"));
  CHECK(logged("no clicker login"));
  CHECK(answer(app, 8000, Kind::Login, 200, "garbage"));
  CHECK(logged("Login reply was not understood"));
  CHECK(!logged(kSecret));

  // Wi-Fi drops while a login waits for its reply: back online, it logs in at once.
  ClickerApp lost;
  powerOn(lost, 0);
  CHECK(lost.nextRequest(0, req) && req.kind == Kind::Login);
  lost.setWifi(false, 100);
  CHECK(!lost.nextRequest(150, req)); // no Wi-Fi, no request
  lost.setWifi(true, 200);
  CHECK(lost.nextRequest(200, req) && req.kind == Kind::Login);

  // Logged in, then the Utz'tutor stops answering: blue slow blink, and it recovers.
  gLog.clear();
  ClickerApp running;
  login(running, 0);
  CHECK(poll(running, 1000, -1, ""));
  CHECK(logged("Utz'tutor did not answer (-1)"));
  CHECK(running.phase() == Phase::Ready);
  CHECK(!running.nextRequest(2999, req)); // retries every 2 s
  CHECK(poll(running, 3000, 502, "bad gateway"));
  CHECK(poll(running, 5000, 200, "garbage"));
  CHECK(logged("Session reply was not understood"));
  CHECK(running.phase() == Phase::ServerUnreachable);
  CHECK(poll(running, 7000, 200, session("s_d", "s_d_r0", "open")));
  CHECK(logged("Utz'tutor answers again"));
  CHECK(running.phase() == Phase::Ready && running.armed());
  CHECK(!logged(kSecret) && !logged(kToken));
}

void test_app_session()
{
  test_session_ended();
  test_server_problems();
}
