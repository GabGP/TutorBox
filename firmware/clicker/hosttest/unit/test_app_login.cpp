// ClickerApp: Wi-Fi, the login, waiting for the teacher, refused logins and lockouts.
#include <string.h>

#include "app_fixture.h"
#include "check.h"

static void test_logs_in_and_waits_for_teacher()
{
  printf("ClickerApp: Wi-Fi, login, unassigned, assigned\n");
  gLog.clear();
  ClickerApp app;
  app.begin("ESP32-T", "2.1.0", kSecret, captureLog, 0);
  Request req;

  CHECK(!app.nextRequest(0, req)); // no Wi-Fi, no network work
  CHECK(app.ledColor(0) == StatusLed::Blue);
  CHECK(app.ledColor(160) == StatusLed::Off); // fast blink
  CHECK(app.statusLedOn(0) && !app.statusLedOn(160));
  CHECK(strcmp(app.phaseName(), "looking-for-wifi") == 0);

  app.setWifi(true, 1000);
  app.setVitals(-60, -1);
  CHECK(app.phase() == Phase::Connecting);
  gLog.clear();
  app.setWifi(true, 1000); // every loop reports Wi-Fi: no change, nothing happens
  CHECK(gLog.empty() && app.phase() == Phase::Connecting);
  CHECK(app.ledColor(1000) == StatusLed::Blue && app.ledColor(1900) == StatusLed::Blue);
  CHECK(app.nextRequest(1000, req) && req.kind == Kind::Login);
  CHECK(req.post && req.bearer == nullptr);
  CHECK(strcmp(req.path, "/api/v1/devices/auth") == 0);
  CHECK(strstr(req.body, kSecret) != nullptr); // the secret goes in the body only
  CHECK(!app.nextRequest(1001, req));          // one request at a time

  app.onResponse(Kind::Login, 403, kUnassigned, 1010);
  CHECK(app.phase() == Phase::Unassigned);
  CHECK(logged("Assign ESP32-T to a student in Clickers on /maestro/"));
  CHECK(app.ledColor(1010) == StatusLed::Magenta);
  CHECK(app.ledColor(2020) == StatusLed::Off); // slow blink
  app.onButton('A', 1500);                     // pressing now: magenta x3, nothing sent
  CHECK(app.ledColor(1500) == StatusLed::Magenta);
  CHECK(logged("Button A ignored: this clicker needs the teacher"));
  CHECK(!app.nextRequest(1500, req));
  CHECK(!app.nextRequest(6009, req)); // asks again every 5 s
  gLog.clear();
  CHECK(answer(app, 6010, Kind::Login, 403, kUnassigned));
  CHECK(!logged("Assign ESP32-T")); // said once, not every 5 s

  // The teacher assigns it: the next login gets a token.
  CHECK(answer(app, 11010, Kind::Login, 200, kLoggedIn));
  CHECK(app.phase() == Phase::Ready);
  CHECK(logged("Assigned to ana: ready to vote"));

  // First the heartbeat, so the teacher's lobby shows the clicker at once.
  CHECK(app.nextRequest(11010, req));
  CHECK(req.kind == Kind::Heartbeat && req.post);
  CHECK(strcmp(req.path, "/api/v1/presence/heartbeat") == 0);
  CHECK(req.bearer != nullptr && strcmp(req.bearer, kToken) == 0);
  CHECK(strcmp(req.body, "{\"rssi\":-60}") == 0);
  app.onResponse(req.kind, 204, "", 11020);

  // Then the poll: a GET, public, so it carries no token.
  CHECK(app.nextRequest(11020, req));
  CHECK(req.kind == Kind::Poll && !req.post && req.bearer == nullptr);
  CHECK(strcmp(req.path, "/api/v1/session/current") == 0);
  CHECK(req.body[0] == '\0');
  app.onResponse(req.kind, 404, kNoSession, 11030); // no match yet: that is fine
  CHECK(app.phase() == Phase::Ready && !app.armed());
  CHECK(app.ledColor(11030) == StatusLed::Green); // the "I'm on" blip...
  CHECK(app.ledColor(11130) == StatusLed::Off);   // ...is short

  CHECK(!app.nextRequest(12029, req)); // polls once a second
  CHECK(answer(app, 12030, Kind::Poll, 404, kNoSession));
  CHECK(!app.nextRequest(13029, req));
  app.setVitals(-48, 73);
  CHECK(answer(app, 13030, Kind::Poll, 404, kNoSession));
  CHECK(answer(app, 14030, Kind::Poll, 404, kNoSession));
  CHECK(answer(app, 15030, Kind::Poll, 404, kNoSession));
  CHECK(app.nextRequest(16020, req)); // heartbeat every 5 s, with the newest vitals
  CHECK(req.kind == Kind::Heartbeat);
  CHECK(strcmp(req.body, "{\"rssi\":-48,\"battery_pct\":73}") == 0);
  CHECK(!logged(kSecret) && !logged(kToken));
}

// A refused login is never retried on a timer. A button press asks once more, and a
// restart asks once, as the first boot does. Every refused login counts toward the
// lockout, so each request here is one that a person asked for.
static void test_refused_login()
{
  printf("ClickerApp: refused login, asked again only by a button press\n");
  gLog.clear();
  ClickerApp app;
  powerOn(app, 0);
  Request req;

  // The boot asks once, and the refusal is shown.
  CHECK(answer(app, 0, Kind::Login, 401, kRefused));
  CHECK(app.phase() == Phase::Rejected);
  CHECK(logged("refused this clicker's secret (HTTP 401 Invalid device credentials.)"));
  CHECK(logged("Fix: delete ESP32-T in Clickers on /maestro/, then press any button"));
  CHECK(!logged("USB") && !logged("Swagger"));
  CHECK(app.ledColor(0) == StatusLed::Magenta && app.ledColor(160) == StatusLed::Off);

  // No timer: not after a minute, not after an hour, not when Wi-Fi comes back.
  CHECK(!app.nextRequest(60000, req));
  CHECK(!app.nextRequest(3600000, req));
  app.setWifi(false, 3600001);
  app.setWifi(true, 3600500);
  CHECK(app.phase() == Phase::Rejected);
  CHECK(!app.nextRequest(3600500, req));

  // A press asks once: one login, and a 401 again stops it there.
  app.onButton('B', 4000000);
  CHECK(logged("Button B: asking the Utz'tutor again"));
  CHECK(app.ledColor(4000000) == StatusLed::Magenta);
  CHECK(app.nextRequest(4000000, req) && req.kind == Kind::Login);
  CHECK(!app.nextRequest(4000001, req)); // one request at a time
  app.onResponse(req.kind, 401, kRefused, 4000010);
  CHECK(app.phase() == Phase::Rejected);
  CHECK(!app.nextRequest(4010000, req));
  CHECK(!app.nextRequest(4500000, req));

  // A wrong shape (422) is refused the same way, and the next press asks once more.
  app.onButton('C', 5000000);
  CHECK(answer(app, 5000000, Kind::Login, 422, "{\"detail\":[{\"msg\":\"bad\"}]}"));
  CHECK(app.phase() == Phase::Rejected);
  CHECK(!app.nextRequest(9000000, req));

  // The teacher deleted the row: the next press enrolls the clicker, 403, unassigned.
  app.onButton('D', 6000);
  CHECK(answer(app, 6000, Kind::Login, 403, kUnassigned));
  CHECK(app.phase() == Phase::Unassigned);
  CHECK(logged("Assign ESP32-T to a student in Clickers on /maestro/"));
  CHECK(!app.nextRequest(6001, req)); // asks every 5 s from now on
  app.onButton('A', 6100);            // a press while unassigned sends nothing
  CHECK(!app.nextRequest(6100, req));

  // The teacher assigns it: the next login gets a token.
  CHECK(answer(app, 11000, Kind::Login, 200, kLoggedIn));
  CHECK(app.phase() == Phase::Ready);
  CHECK(!logged(kSecret) && !logged(kToken));

  // A lockout answers 429: the clicker asks again by itself every 30 s, and a press
  // in the lockout asks once more (the Utz'tutor answers 429 again, the timer goes on).
  ClickerApp locked;
  powerOn(locked, 0);
  CHECK(answer(locked, 0, Kind::Login, 401, kRefused));
  locked.onButton('A', 1000);
  CHECK(answer(locked, 1000, Kind::Login, 429, kLockedOut));
  CHECK(locked.phase() == Phase::Rejected);
  CHECK(logged("locked this clicker out"));
  CHECK(!locked.nextRequest(30999, req));
  locked.onButton('B', 31000);
  CHECK(answer(locked, 31000, Kind::Login, 429, kLockedOut));
  CHECK(!locked.nextRequest(60999, req));
  CHECK(answer(locked, 61000, Kind::Login, 200, kLoggedIn)); // the timer, not a press
  CHECK(locked.phase() == Phase::Ready);

  // A restart asks once more, as the first boot did.
  ClickerApp restarted;
  powerOn(restarted, 90000);
  CHECK(answer(restarted, 90000, Kind::Login, 401, kRefused));
  CHECK(!restarted.nextRequest(900000, req));
  CHECK(!logged(kSecret) && !logged(kToken));
}

void test_app_login()
{
  test_logs_in_and_waits_for_teacher();
  test_refused_login();
}
