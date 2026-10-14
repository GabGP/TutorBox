// Unit tests for the clicker's pure logic (no ESP32 needed): ./run_tests.sh
#include <stdio.h>
#include <string.h>

#include <string>
#include <vector>

#include "Buttons.h"
#include "ClickerApp.h"
#include "Protocol.h"
#include "SerialSetup.h"
#include "StatusLed.h"

static int gFailures = 0;
static int gChecks = 0;

#define CHECK(cond)                                                   \
  do {                                                                \
    gChecks++;                                                        \
    if (!(cond)) {                                                    \
      gFailures++;                                                    \
      printf("  FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond);        \
    }                                                                 \
  } while (0)

static std::vector<std::string> gLog;
static void captureLog(const char* line) { gLog.push_back(line); }
static bool logged(const char* fragment) {
  for (size_t i = 0; i < gLog.size(); i++) {
    if (gLog[i].find(fragment) != std::string::npos) return true;
  }
  return false;
}

// ---------------------------------------------------------------------------
// ButtonBank
// ---------------------------------------------------------------------------

struct Pad {
  bool down[4] = {false, false, false, false};
  uint32_t edges[4] = {0, 0, 0, 0};
};

static void test_buttons() {
  printf("ButtonBank\n");
  ButtonBank bank(30);
  Pad pad;

  // Held at power-on: ignored until released.
  pad.down[0] = true;
  CHECK(bank.update(pad.down, pad.edges, 0) == 0);
  CHECK(bank.update(pad.down, pad.edges, 500) == 0);
  pad.down[0] = false;
  CHECK(bank.update(pad.down, pad.edges, 510) == 0);
  CHECK(bank.update(pad.down, pad.edges, 545) == 0);  // re-armed here, no press

  // Press seen by the interrupt: reported at once, exactly once.
  pad.down[1] = true;
  pad.edges[1]++;
  CHECK(bank.update(pad.down, pad.edges, 600) == 'B');
  pad.edges[1] += 3;  // bounce while pressed
  CHECK(bank.update(pad.down, pad.edges, 602) == 0);
  CHECK(bank.update(pad.down, pad.edges, 900) == 0);  // long hold: still one press
  pad.down[1] = false;
  pad.edges[1] += 2;  // release bounce
  CHECK(bank.update(pad.down, pad.edges, 905) == 0);
  CHECK(bank.update(pad.down, pad.edges, 940) == 0);  // steady release: re-armed
  pad.down[1] = true;
  pad.edges[1]++;
  CHECK(bank.update(pad.down, pad.edges, 1000) == 'B');  // the next real press
  pad.down[1] = false;
  CHECK(bank.update(pad.down, pad.edges, 1100) == 0);
  CHECK(bank.update(pad.down, pad.edges, 1140) == 0);

  // A tap the loop never saw (it was busy on the network): the edge counts.
  pad.edges[2]++;
  CHECK(bank.update(pad.down, pad.edges, 2000) == 'C');
  CHECK(bank.update(pad.down, pad.edges, 2040) == 0);

  // No interrupt (it missed): a press held for 30 ms still counts.
  pad.down[3] = true;
  CHECK(bank.update(pad.down, pad.edges, 3000) == 0);
  CHECK(bank.update(pad.down, pad.edges, 3029) == 0);
  CHECK(bank.update(pad.down, pad.edges, 3030) == 'D');
  pad.down[3] = false;
  CHECK(bank.update(pad.down, pad.edges, 3100) == 0);
  CHECK(bank.update(pad.down, pad.edges, 3140) == 0);

  // Two buttons in the same instant: A wins, B is dropped, not reported later.
  pad.down[0] = pad.down[1] = true;
  pad.edges[0]++;
  pad.edges[1]++;
  CHECK(bank.update(pad.down, pad.edges, 4000) == 'A');
  CHECK(bank.update(pad.down, pad.edges, 4100) == 0);
  pad.down[0] = pad.down[1] = false;
  CHECK(bank.update(pad.down, pad.edges, 4200) == 0);
  CHECK(bank.update(pad.down, pad.edges, 4240) == 0);

  // Works across the 49-day millis() wrap.
  ButtonBank wrap(30);
  Pad pad2;
  const uint32_t t0 = 0xFFFFFFF0u;
  CHECK(wrap.update(pad2.down, pad2.edges, t0) == 0);
  CHECK(wrap.update(pad2.down, pad2.edges, t0 + 40) == 0);  // wraps to 0x18
  pad2.edges[0]++;
  CHECK(wrap.update(pad2.down, pad2.edges, t0 + 50) == 'A');
}

// ---------------------------------------------------------------------------
// StatusLed
// ---------------------------------------------------------------------------

static void test_led() {
  printf("StatusLed\n");
  StatusLed led;
  CHECK(led.colorAt(0) == StatusLed::Off);

  led.setPattern(StatusLed::Blue, 150, 150, 1000);
  CHECK(led.colorAt(1000) == StatusLed::Blue);
  CHECK(led.colorAt(1149) == StatusLed::Blue);
  CHECK(led.colorAt(1150) == StatusLed::Off);
  CHECK(led.colorAt(1300) == StatusLed::Blue);
  led.setPattern(StatusLed::Blue, 150, 150, 1200);  // same pattern: rhythm kept
  CHECK(led.colorAt(1200) == StatusLed::Off);

  led.setPattern(StatusLed::White, 1, 0, 2000);  // steady
  CHECK(led.colorAt(9999) == StatusLed::White);
  led.setPattern(StatusLed::Green, 0, 100, 2000);  // onMs 0 = dark
  CHECK(led.colorAt(2000) == StatusLed::Off);

  led.setPattern(StatusLed::Green, 60, 2940, 3000);
  led.flash(StatusLed::Green, 1500, 3000);
  CHECK(led.overlayActive(3000));
  CHECK(led.colorAt(3500) == StatusLed::Green);  // overlay, not the blip's dark part
  CHECK(led.colorAt(4499) == StatusLed::Green);
  CHECK(!led.overlayActive(4500));
  CHECK(led.colorAt(4500) == StatusLed::Off);  // back to the blip (dark here)

  led.blink(StatusLed::Red, 3, 10000);
  CHECK(led.colorAt(10000) == StatusLed::Red);
  CHECK(led.colorAt(10150) == StatusLed::Off);
  CHECK(led.colorAt(10300) == StatusLed::Red);
  CHECK(led.colorAt(10600) == StatusLed::Red);
  CHECK(led.colorAt(10750) == StatusLed::Off);
  CHECK(led.overlayActive(10899));
  CHECK(!led.overlayActive(10900));
}

// ---------------------------------------------------------------------------
// Protocol
// ---------------------------------------------------------------------------

static const char* kSecret = "0123456789abcdef0123456789abcdef";
static const char* kToken = "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d";
static const char* kLoggedIn =
    "{\"session_id\":\"9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d\",\"username\":\"ana\","
    "\"device_id\":\"ESP32-T\"}";
static const char* kUnassigned = "{\"detail\":\"Device is not assigned to any student.\"}";
static const char* kNoSession = "{\"detail\":\"No active session.\"}";

// GET /session/current as the backend sends it, question text included.
static std::string session(const char* sessionId, const char* roundId,
                           const char* status) {
  std::string s = std::string("{\"id\":\"") + sessionId +
                  "\",\"title\":\"Repaso\",\"topic\":\"arithmetic\",\"status\":\"active\","
                  "\"current_round_index\":0,\"question_count\":3,\"current_round\":";
  if (roundId == nullptr) return s + "null}";
  s += std::string("{\"round_id\":\"") + roundId + "\",\"round_index\":0,\"status\":\"" +
       status +
       "\",\"question_id\":\"q_add_001\",\"duration_seconds\":20,"
       "\"time_remaining\":12.5,\"votes_cast\":7,\"question\":{\"question_text\":"
       "\"\\u00bfCu\\u00e1nto es 54 + 38?\",\"options\":{\"A\":\"82\",\"B\":\"16\","
       "\"C\":\"92\",\"D\":\"812\"}},\"result\":null}}";
  return s;
}

static void test_protocol() {
  printf("Protocol\n");
  char out[192];

  CHECK(protocol::isSecret(kSecret));
  CHECK(!protocol::isSecret("0123456789ABCDEF0123456789ABCDEF"));  // upper case
  CHECK(!protocol::isSecret("0123456789abcdef0123456789abcde"));   // 31
  CHECK(!protocol::isSecret("0123456789abcdef0123456789abcdef0"));  // 33
  CHECK(!protocol::isSecret("0123456789abcdef0123456789abcdeg"));  // not hex
  CHECK(!protocol::isSecret(""));
  CHECK(!protocol::isSecret(nullptr));

  CHECK(protocol::batteryPercent(3750, 3300, 4200) == 50);
  CHECK(protocol::batteryPercent(3300, 3300, 4200) == 0);
  CHECK(protocol::batteryPercent(2900, 3300, 4200) == 0);
  CHECK(protocol::batteryPercent(4200, 3300, 4200) == 100);
  CHECK(protocol::batteryPercent(4350, 3300, 4200) == 100);
  CHECK(protocol::batteryPercent(-1, 3300, 4200) == -1);   // not fitted
  CHECK(protocol::batteryPercent(3750, 4200, 4200) == -1);  // settings make no sense

  protocol::authBody(out, sizeof(out), "ESP32-A4CF12", kSecret);
  CHECK(strcmp(out,
               "{\"device_id\":\"ESP32-A4CF12\","
               "\"secret\":\"0123456789abcdef0123456789abcdef\"}") == 0);

  protocol::heartbeatBody(out, sizeof(out), -55, 88);
  CHECK(strcmp(out, "{\"rssi\":-55,\"battery_pct\":88}") == 0);
  protocol::heartbeatBody(out, sizeof(out), -55, -1);
  CHECK(strcmp(out, "{\"rssi\":-55}") == 0);
  protocol::heartbeatBody(out, sizeof(out), 0, -1);  // Wi-Fi reports 0 when unknown
  CHECK(strcmp(out, "{}") == 0);
  protocol::heartbeatBody(out, sizeof(out), -130, 101);  // outside what the API takes
  CHECK(strcmp(out, "{}") == 0);

  protocol::voteBody(out, sizeof(out), 'C', 1234);
  CHECK(strcmp(out, "{\"selected_option\":\"C\",\"response_time_ms\":1234}") == 0);
  char path[protocol::kPathSize];
  protocol::votePath(path, sizeof(path), "s_a1b2c3d4e5f6");
  CHECK(strcmp(path, "/api/v1/session/s_a1b2c3d4e5f6/vote") == 0);

  char token[protocol::kTokenSize] = "";
  char username[protocol::kUsernameSize] = "";
  CHECK(protocol::parseAuth(kLoggedIn, token, sizeof(token), username,
                            sizeof(username)));
  CHECK(strcmp(token, kToken) == 0);
  CHECK(strcmp(username, "ana") == 0);
  token[0] = '\0';
  CHECK(!protocol::parseAuth("not json", token, sizeof(token), username,
                             sizeof(username)));
  CHECK(!protocol::parseAuth(kUnassigned, token, sizeof(token), username,
                             sizeof(username)));
  // A token that does not fit is refused whole, never cut.
  std::string longToken = "{\"session_id\":\"" + std::string(200, 't') + "\"}";
  CHECK(!protocol::parseAuth(longToken.c_str(), token, sizeof(token), username,
                             sizeof(username)));
  CHECK(token[0] == '\0');

  protocol::SessionView view;
  CHECK(protocol::parseSession(session("s_x", "s_x_r0", "open").c_str(), view));
  CHECK(view.roundOpen);
  CHECK(strcmp(view.sessionId, "s_x") == 0);
  CHECK(strcmp(view.roundId, "s_x_r0") == 0);
  CHECK(protocol::parseSession(session("s_x", "s_x_r0", "revealed").c_str(), view));
  CHECK(!view.roundOpen && strcmp(view.roundId, "s_x_r0") == 0);
  CHECK(protocol::parseSession(session("s_x", "s_x_r0", "pending").c_str(), view));
  CHECK(!view.roundOpen);  // the lobby: the first question is not open yet
  CHECK(protocol::parseSession(session("s_x", nullptr, "").c_str(), view));
  CHECK(!view.roundOpen && view.roundId[0] == '\0');
  CHECK(!protocol::parseSession("not json", view));
  CHECK(!protocol::parseSession(kNoSession, view));
  std::string longRound(200, 'r');
  CHECK(!protocol::parseSession(session("s_x", longRound.c_str(), "open").c_str(),
                                view));

  char detail[32];
  CHECK(protocol::parseDetail("{\"detail\":\"Round not found.\"}", detail,
                              sizeof(detail)));
  CHECK(strcmp(detail, "Round not found.") == 0);
  CHECK(!protocol::parseDetail("{\"detail\":[{\"msg\":\"bad\"}]}", detail,
                               sizeof(detail)));
  CHECK(!protocol::parseDetail("", detail, sizeof(detail)));

  CHECK(protocol::isAlreadyVoted("Student 4 has already voted in round s_x_r0."));
  CHECK(!protocol::isAlreadyVoted("Round 's_x_r0' is not open."));
  CHECK(!protocol::isAlreadyVoted("Voting window has expired."));
  CHECK(!protocol::isAlreadyVoted(""));
  CHECK(!protocol::isAlreadyVoted(nullptr));
}

// ---------------------------------------------------------------------------
// SerialSetup
// ---------------------------------------------------------------------------

// Types `text` on the setup link and returns what its last character produced.
static SerialSetup::Command type(SerialSetup& link, const std::string& text) {
  SerialSetup::Command last = SerialSetup::Command::None;
  for (size_t i = 0; i < text.size(); i++) last = link.feed(text[i]);
  return last;
}

static void test_serial_setup() {
  printf("SerialSetup\n");
  SerialSetup link;
  const std::string secretLine = std::string("secret ") + kSecret;

  CHECK(type(link, "id") == SerialSetup::Command::None);  // no Enter yet
  CHECK(link.feed('\n') == SerialSetup::Command::Identify);
  CHECK(link.feed('i') == SerialSetup::Command::None);
  CHECK(link.feed('d') == SerialSetup::Command::None);
  CHECK(link.feed('\r') == SerialSetup::Command::Identify);  // Windows line ending:
  CHECK(link.feed('\n') == SerialSetup::Command::None);      // its "\n" is not a line

  CHECK(type(link, secretLine + "\n") == SerialSetup::Command::Secret);
  CHECK(strcmp(link.secret(), kSecret) == 0);
  link.forget();
  CHECK(link.secret()[0] == '\0');

  CHECK(type(link, "secret\n") == SerialSetup::Command::BadSecret);
  CHECK(type(link, "secret 1234\n") == SerialSetup::Command::BadSecret);
  CHECK(type(link, "secret  0123456789abcdef0123456789abcde\n") ==
        SerialSetup::Command::BadSecret);  // two spaces
  CHECK(type(link, secretLine + "0\n") == SerialSetup::Command::BadSecret);
  CHECK(link.secret()[0] == '\0');  // a refused line leaves no secret behind

  CHECK(type(link, "hello\n") == SerialSetup::Command::Unknown);
  CHECK(type(link, "ID\n") == SerialSetup::Command::Unknown);

  // A line longer than any command is dropped whole, even if it starts like one.
  CHECK(type(link, secretLine + std::string(100, 'f') + "\n") ==
        SerialSetup::Command::Unknown);
  CHECK(type(link, "id\n") == SerialSetup::Command::Identify);  // and the link recovers
}

// ---------------------------------------------------------------------------
// ClickerApp
// ---------------------------------------------------------------------------

typedef ClickerApp::RequestKind Kind;
typedef ClickerApp::Phase Phase;

// Takes the next request, which must be of `kind`, and answers it.
static bool answer(ClickerApp& app, uint32_t now, Kind kind, int status,
                   const char* body) {
  ClickerApp::Request req;
  if (!app.nextRequest(now, req) || req.kind != kind) return false;
  app.onResponse(req.kind, status, body, now);
  return true;
}

// Answers the poll that is due at `now`, and the heartbeat first if one is due too.
static bool poll(ClickerApp& app, uint32_t now, int status, const std::string& body) {
  ClickerApp::Request req;
  if (!app.nextRequest(now, req)) return false;
  if (req.kind == Kind::Heartbeat) {
    app.onResponse(req.kind, 204, "", now);
    if (!app.nextRequest(now, req)) return false;
  }
  if (req.kind != Kind::Poll) return false;
  app.onResponse(req.kind, status, body.c_str(), now);
  return true;
}

// Powers on with a secret, joins Wi-Fi and logs in; no match is running.
static void login(ClickerApp& app, uint32_t now) {
  app.begin("ESP32-T", "2.0.0", kSecret, captureLog, now);
  app.setWifi(true, now);
  CHECK(answer(app, now, Kind::Auth, 200, kLoggedIn));
  CHECK(answer(app, now, Kind::Heartbeat, 204, ""));
  CHECK(answer(app, now, Kind::Poll, 404, kNoSession));
  CHECK(app.phase() == Phase::Ready);
}

static void test_app_needs_secret() {
  printf("ClickerApp: no secret yet, USB setup\n");
  gLog.clear();
  ClickerApp app;
  app.begin("ESP32-T", "2.0.0", "", captureLog, 0);
  ClickerApp::Request req;

  app.setWifi(true, 1000);
  CHECK(app.phase() == Phase::NeedsSecret);
  CHECK(logged("No secret yet: set ESP32-T up over USB"));
  CHECK(!app.nextRequest(1000, req));    // nothing to log in with
  CHECK(!app.nextRequest(600000, req));  // ever
  CHECK(app.ledColor(1000) == StatusLed::Magenta);
  CHECK(app.ledColor(1160) == StatusLed::Off);  // fast blink
  app.onButton('A', 2000);
  CHECK(logged("this clicker needs the teacher"));
  CHECK(app.ledColor(2000) == StatusLed::Magenta);

  app.setSecret("not a secret", 3000);  // ignored
  CHECK(app.phase() == Phase::NeedsSecret);
  app.setSecret(kSecret, 3000);
  CHECK(logged("New secret stored"));
  CHECK(app.phase() == Phase::Connecting);
  CHECK(app.nextRequest(3000, req));
  CHECK(req.kind == Kind::Auth && req.post && req.bearer == nullptr);
  CHECK(strcmp(req.path, "/api/v1/devices/auth") == 0);
  CHECK(strcmp(req.body,
               "{\"device_id\":\"ESP32-T\","
               "\"secret\":\"0123456789abcdef0123456789abcdef\"}") == 0);

  // Flash held something that is not a secret: same as none.
  ClickerApp damaged;
  damaged.begin("ESP32-T", "2.0.0", "ffff", captureLog, 0);
  damaged.setWifi(true, 0);
  CHECK(damaged.phase() == Phase::NeedsSecret);

  // The secret arrives before Wi-Fi does: it logs in once Wi-Fi is up.
  ClickerApp early;
  early.begin("ESP32-T", "2.0.0", "", captureLog, 0);
  early.setSecret(kSecret, 100);
  CHECK(early.phase() == Phase::LookingForWifi);
  CHECK(!early.nextRequest(100, req));
  early.setWifi(true, 200);
  CHECK(early.phase() == Phase::Connecting);
  CHECK(early.nextRequest(200, req) && req.kind == Kind::Auth);
  CHECK(!logged(kSecret));  // the secret is never written to the log
}

static void test_app_logs_in_and_waits_for_teacher() {
  printf("ClickerApp: Wi-Fi, login, unassigned, assigned\n");
  gLog.clear();
  ClickerApp app;
  app.begin("ESP32-T", "2.0.0", kSecret, captureLog, 0);
  ClickerApp::Request req;

  CHECK(!app.nextRequest(0, req));  // no Wi-Fi, no network work
  CHECK(app.ledColor(0) == StatusLed::Blue);
  CHECK(app.ledColor(160) == StatusLed::Off);  // fast blink
  CHECK(app.statusLedOn(0) && !app.statusLedOn(160));

  app.setWifi(true, 1000);
  app.setVitals(-60, -1);
  CHECK(app.phase() == Phase::Connecting);
  CHECK(app.ledColor(1000) == StatusLed::Blue && app.ledColor(1900) == StatusLed::Blue);
  CHECK(app.nextRequest(1000, req) && req.kind == Kind::Auth);
  CHECK(!app.nextRequest(1001, req));  // one request at a time

  app.onResponse(Kind::Auth, 403, kUnassigned, 1010);
  CHECK(app.phase() == Phase::Unassigned);
  CHECK(logged("Waiting for the teacher to assign ESP32-T"));
  CHECK(app.ledColor(1010) == StatusLed::Magenta);
  CHECK(app.ledColor(2020) == StatusLed::Off);  // slow blink
  app.onButton('A', 1500);                      // pressing now: magenta x3, nothing sent
  CHECK(app.ledColor(1500) == StatusLed::Magenta);
  CHECK(!app.nextRequest(1500, req));
  CHECK(!app.nextRequest(6009, req));  // asks again every 5 s
  CHECK(answer(app, 6010, Kind::Auth, 403, kUnassigned));

  // The teacher assigns it: the next login gets a token.
  CHECK(answer(app, 11010, Kind::Auth, 200, kLoggedIn));
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
  app.onResponse(req.kind, 404, kNoSession, 11030);  // no match yet: that is fine
  CHECK(app.phase() == Phase::Ready && !app.armed());
  CHECK(app.ledColor(11030) == StatusLed::Green);  // the "I'm on" blip...
  CHECK(app.ledColor(11130) == StatusLed::Off);    // ...is short

  CHECK(!app.nextRequest(12029, req));  // polls once a second
  CHECK(answer(app, 12030, Kind::Poll, 404, kNoSession));
  CHECK(!app.nextRequest(13029, req));
  app.setVitals(-48, 73);
  CHECK(answer(app, 13030, Kind::Poll, 404, kNoSession));
  CHECK(answer(app, 14030, Kind::Poll, 404, kNoSession));
  CHECK(answer(app, 15030, Kind::Poll, 404, kNoSession));
  CHECK(app.nextRequest(16020, req));  // heartbeat every 5 s, with the newest vitals
  CHECK(req.kind == Kind::Heartbeat);
  CHECK(strcmp(req.body, "{\"rssi\":-48,\"battery_pct\":73}") == 0);
  CHECK(!logged(kSecret) && !logged(kToken));
}

static void test_app_votes() {
  printf("ClickerApp: open question, vote, second press\n");
  gLog.clear();
  ClickerApp app;
  login(app, 0);
  ClickerApp::Request req;

  app.onButton('B', 50);  // no question yet: red x3 (until 950 ms)
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
  CHECK(app.ledColor(3200) == StatusLed::Yellow);
  CHECK(app.nextRequest(3200, req));
  CHECK(req.kind == Kind::Vote && req.post);
  CHECK(strcmp(req.path, "/api/v1/session/s_a/vote") == 0);
  CHECK(req.bearer != nullptr && strcmp(req.bearer, kToken) == 0);
  CHECK(strcmp(req.body, "{\"selected_option\":\"C\",\"response_time_ms\":1200}") == 0);
  app.onButton('D', 3210);             // while sending: ignored
  CHECK(!app.nextRequest(3220, req));  // nothing else while the vote is in flight

  app.onResponse(Kind::Vote, 200, "{}", 3230);
  CHECK(logged("Vote C counted"));
  CHECK(app.ledColor(3230) == StatusLed::Green);
  CHECK(app.ledColor(4700) == StatusLed::Green);  // 1.5 s of green
  CHECK(!app.armed());                            // answered: this round is done

  app.onButton('A', 4800);  // second press in the same round
  CHECK(logged("already answered"));
  CHECK(app.ledColor(4800) == StatusLed::Red);
  CHECK(poll(app, 4800, 200, session("s_a", "s_a_r0", "open")));
  CHECK(!app.armed());  // the round is still open on the server: still done for us

  CHECK(poll(app, 6000, 200, session("s_a", "s_a_r0", "revealed")));
  CHECK(!app.armed());
  CHECK(poll(app, 7000, 200, session("s_a", "s_a_r1", "open")));  // next question
  CHECK(app.armed());
  CHECK(poll(app, 8000, 200, session("s_a", "s_a_r1", "closed")));  // time is up
  CHECK(!app.armed());
  CHECK(poll(app, 9000, 404, kNoSession));  // the match ended
  CHECK(!app.armed() && app.phase() == Phase::Ready);
}

static void test_app_vote_errors() {
  printf("ClickerApp: 409, retries, lost Wi-Fi, session ended mid-vote\n");
  gLog.clear();
  ClickerApp app;
  login(app, 0);
  ClickerApp::Request req;
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
  app.onResponse(req.kind, -11, "", 2200);  // read timeout
  CHECK(logged("retrying"));
  CHECK(!app.nextRequest(2300, req));  // waits 250 ms, nothing else meanwhile
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
  for (int i = 0; i < 3; i++) {
    CHECK(app.nextRequest(t, req) && req.kind == Kind::Vote);
    app.onResponse(req.kind, -1, "", t);
    t += 300;
  }
  CHECK(logged("Vote C failed"));
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
  CHECK(app.phase() == Phase::Ready && !app.armed());  // not armed on old news
  CHECK(answer(app, 9000, Kind::Heartbeat, 204, ""));
  CHECK(poll(app, 9000, 200, session("s_b", "s_b_r4", "open")));
  CHECK(app.armed());

  // The session ended under a vote (401): log in again, then send the same vote.
  app.onButton('A', 9100);
  CHECK(app.nextRequest(9100, req) && req.kind == Kind::Vote);
  app.onResponse(req.kind, 401, "{\"detail\":\"Invalid or expired session.\"}", 9110);
  CHECK(logged("Vote A: the session ended, logging in again"));
  CHECK(app.phase() == Phase::Connecting);
  CHECK(answer(app, 9110, Kind::Auth, 200, kLoggedIn));
  CHECK(app.nextRequest(9120, req) && req.kind == Kind::Vote);
  CHECK(strcmp(req.path, "/api/v1/session/s_b/vote") == 0);
  app.onResponse(req.kind, 200, "{}", 9130);
  CHECK(logged("Vote A counted"));

  // Same, but the teacher took the clicker away: the vote is dropped and shown.
  CHECK(poll(app, 11000, 200, session("s_b", "s_b_r5", "open")));
  app.onButton('B', 11100);
  CHECK(app.nextRequest(11100, req) && req.kind == Kind::Vote);
  app.onResponse(req.kind, 401, "{\"detail\":\"Invalid or expired session.\"}", 11110);
  CHECK(answer(app, 11110, Kind::Auth, 403, kUnassigned));
  CHECK(logged("Vote B was NOT sent (no session)"));
  CHECK(app.phase() == Phase::Unassigned);
  CHECK(app.ledColor(11110) == StatusLed::Magenta);
  CHECK(!app.nextRequest(11120, req));  // no vote, and the next login is 5 s away
}

static void test_app_session_ended() {
  printf("ClickerApp: unassigned or reassigned while it runs\n");
  gLog.clear();
  ClickerApp app;
  login(app, 0);
  ClickerApp::Request req;
  CHECK(poll(app, 1000, 200, session("s_c", "s_c_r0", "open")));
  CHECK(app.armed());

  // The heartbeat is what tells a clicker that the teacher took it away.
  CHECK(answer(app, 5000, Kind::Heartbeat, 401,
               "{\"detail\":\"Invalid or expired session.\"}"));
  CHECK(logged("TutorBox ended this clicker's session"));
  CHECK(app.phase() == Phase::Connecting && !app.armed());
  CHECK(answer(app, 5000, Kind::Auth, 403, kUnassigned));
  CHECK(app.phase() == Phase::Unassigned);
  CHECK(!app.nextRequest(5001, req));  // no polls and no heartbeats without a token

  // Assigned to another student: a new token, voting again.
  CHECK(answer(app, 10000, Kind::Auth, 200, kLoggedIn));
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
}

static void test_app_server_problems() {
  printf("ClickerApp: server down, refused secret, lockout\n");
  gLog.clear();
  ClickerApp app;
  app.begin("ESP32-T", "2.0.0", kSecret, captureLog, 0);
  app.setWifi(true, 0);
  ClickerApp::Request req;

  CHECK(answer(app, 0, Kind::Auth, -1, ""));
  CHECK(app.phase() == Phase::Connecting);
  CHECK(!app.nextRequest(1500, req));  // retries every 2 s
  CHECK(answer(app, 2000, Kind::Auth, 502, "bad gateway"));
  CHECK(answer(app, 4000, Kind::Auth, -1, ""));
  CHECK(app.phase() == Phase::ServerUnreachable);
  CHECK(app.ledColor(4000) == StatusLed::Blue && app.ledColor(5100) == StatusLed::Off);
  app.onButton('A', 5200);
  CHECK(logged("not connected yet"));

  CHECK(answer(app, 6000, Kind::Auth, 404, "{\"detail\":\"Not Found\"}"));
  CHECK(logged("no clicker login"));
  CHECK(answer(app, 8000, Kind::Auth, 200, "garbage"));
  CHECK(logged("Login reply was not understood"));

  // A refused secret: one try, then silence. More tries would only lock it out.
  CHECK(answer(app, 10000, Kind::Auth, 401,
               "{\"detail\":\"Invalid device credentials.\"}"));
  CHECK(app.phase() == Phase::Rejected);
  CHECK(logged("refused this clicker's secret (HTTP 401 Invalid device credentials.)"));
  CHECK(logged("Fix: set ESP32-T up again over USB"));
  CHECK(app.ledColor(10000) == StatusLed::Magenta);
  CHECK(!app.nextRequest(12000, req));
  CHECK(!app.nextRequest(3600000, req));
  app.setWifi(false, 3600001);  // not even after Wi-Fi comes back
  app.setWifi(true, 3600500);
  CHECK(app.phase() == Phase::Rejected);
  CHECK(!app.nextRequest(3600500, req));

  // A new secret over USB: it tries again. The TutorBox had locked it out: it waits.
  const uint32_t t = 3700000;
  app.setSecret("ffffffffffffffffffffffffffffffff", t);
  CHECK(app.phase() == Phase::Connecting);
  CHECK(app.nextRequest(t, req) && req.kind == Kind::Auth);
  CHECK(strstr(req.body, "ffffffffffffffffffffffffffffffff") != nullptr);
  app.onResponse(req.kind, 429, "{\"detail\":\"Too many failed login attempts.\"}", t);
  CHECK(app.phase() == Phase::Rejected);
  CHECK(logged("locked this clicker out"));
  CHECK(!app.nextRequest(t + 29999, req));
  CHECK(answer(app, t + 30000, Kind::Auth, 200, kLoggedIn));
  CHECK(app.phase() == Phase::Ready);

  // A secret of the wrong shape (422) is refused like a wrong one.
  ClickerApp other;
  other.begin("ESP32-T", "2.0.0", kSecret, captureLog, 0);
  other.setWifi(true, 0);
  CHECK(answer(other, 0, Kind::Auth, 422, "{\"detail\":[{\"msg\":\"bad\"}]}"));
  CHECK(other.phase() == Phase::Rejected);
  CHECK(!other.nextRequest(60000, req));

  // Logged in, then the TutorBox stops answering: blue slow blink, and it recovers.
  gLog.clear();
  ClickerApp running;
  login(running, 0);
  CHECK(poll(running, 1000, -1, ""));
  CHECK(running.phase() == Phase::Ready);
  CHECK(!running.nextRequest(2999, req));  // retries every 2 s
  CHECK(poll(running, 3000, 502, "bad gateway"));
  CHECK(poll(running, 5000, 200, "garbage"));
  CHECK(logged("Session reply was not understood"));
  CHECK(running.phase() == Phase::ServerUnreachable);
  CHECK(poll(running, 7000, 200, session("s_d", "s_d_r0", "open")));
  CHECK(logged("TutorBox answers again"));
  CHECK(running.phase() == Phase::Ready && running.armed());
  CHECK(!logged(kSecret) && !logged(kToken));
}

int main() {
  test_buttons();
  test_led();
  test_protocol();
  test_serial_setup();
  test_app_needs_secret();
  test_app_logs_in_and_waits_for_teacher();
  test_app_votes();
  test_app_vote_errors();
  test_app_session_ended();
  test_app_server_problems();
  printf("\n%d checks, %d failures\n", gChecks, gFailures);
  return gFailures == 0 ? 0 : 1;
}
