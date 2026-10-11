// Unit tests for the clicker's pure logic (no ESP32 needed): ./run_tests.sh
#include <stdio.h>
#include <string.h>

#include <string>
#include <vector>

#include "Buttons.h"
#include "ClickerApp.h"
#include "Protocol.h"
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

static void test_protocol() {
  printf("Protocol\n");
  char out[192];

  protocol::checkinBody(out, sizeof(out), "1.0.0", -55, 3950);
  CHECK(strcmp(out, "{\"firmware\":\"1.0.0\",\"rssi\":-55,\"battery_mv\":3950}") == 0);
  protocol::checkinBody(out, sizeof(out), "1.0.0", 0, -1);
  CHECK(strcmp(out, "{\"firmware\":\"1.0.0\"}") == 0);

  protocol::voteBody(out, sizeof(out), "s_abc_r2", 'C', 1234);
  CHECK(strcmp(out,
               "{\"round_id\":\"s_abc_r2\",\"selected_option\":\"C\","
               "\"response_time_ms\":1234}") == 0);

  protocol::CheckinReply reply;
  CHECK(protocol::parseCheckin(
      "{\"device_id\":\"ESP32-A1\",\"assigned\":true,\"round_id\":\"s_x_r0\","
      "\"round_open\":true,\"voted\":false}",
      reply));
  CHECK(reply.assigned && reply.roundOpen && !reply.voted);
  CHECK(strcmp(reply.roundId, "s_x_r0") == 0);

  CHECK(protocol::parseCheckin(
      "{\"assigned\":false,\"round_id\":null,\"round_open\":false,\"voted\":false}",
      reply));
  CHECK(!reply.assigned && reply.roundId[0] == '\0');

  CHECK(!protocol::parseCheckin("not json", reply));
  CHECK(!protocol::parseCheckin("{\"detail\":\"Not Found\"}", reply));

  std::string longId(200, 'r');
  std::string json = "{\"assigned\":true,\"round_id\":\"" + longId + "\"}";
  CHECK(protocol::parseCheckin(json.c_str(), reply));
  CHECK(strlen(reply.roundId) == protocol::kRoundIdSize - 1);

  char detail[32];
  CHECK(protocol::parseDetail("{\"detail\":\"Round not found.\"}", detail,
                              sizeof(detail)));
  CHECK(strcmp(detail, "Round not found.") == 0);
  CHECK(!protocol::parseDetail("{\"detail\":[{\"msg\":\"bad\"}]}", detail,
                               sizeof(detail)));
  CHECK(!protocol::parseDetail("", detail, sizeof(detail)));
}

// ---------------------------------------------------------------------------
// ClickerApp
// ---------------------------------------------------------------------------

static const char* kUnassigned =
    "{\"device_id\":\"ESP32-T\",\"assigned\":false,\"round_id\":null,"
    "\"round_open\":false,\"voted\":false}";

static std::string reply(const char* roundId, bool open, bool voted) {
  std::string r = "{\"device_id\":\"ESP32-T\",\"assigned\":true,\"round_id\":";
  r += roundId ? std::string("\"") + roundId + "\"" : "null";
  r += open ? ",\"round_open\":true" : ",\"round_open\":false";
  r += voted ? ",\"voted\":true}" : ",\"voted\":false}";
  return r;
}

// Sends the pending check-in (if due) and answers it with `status`/`body`.
static bool answerCheckin(ClickerApp& app, uint32_t now, int status, const char* body) {
  ClickerApp::Request req;
  if (!app.nextRequest(now, req) || req.kind != ClickerApp::RequestKind::Checkin) {
    return false;
  }
  app.onResponse(req.kind, status, body, now);
  return true;
}

static void test_app_connects_and_waits_for_teacher() {
  printf("ClickerApp: Wi-Fi, check-in, unassigned\n");
  gLog.clear();
  ClickerApp app;
  app.begin("ESP32-T", "1.0.0", captureLog, 0);
  ClickerApp::Request req;

  CHECK(!app.nextRequest(0, req));  // no Wi-Fi, no network work
  CHECK(app.ledColor(0) == StatusLed::Blue);
  CHECK(app.ledColor(160) == StatusLed::Off);  // fast blink
  CHECK(app.statusLedOn(0) && !app.statusLedOn(160));

  app.setWifi(true, 1000);
  app.setVitals(-60, -1);
  CHECK(app.phase() == ClickerApp::Phase::Connecting);
  CHECK(app.ledColor(1000) == StatusLed::Blue && app.ledColor(1900) == StatusLed::Blue);
  CHECK(app.nextRequest(1000, req));
  CHECK(req.kind == ClickerApp::RequestKind::Checkin);
  CHECK(strcmp(req.path, "/api/v1/clicker/checkin") == 0);
  CHECK(strcmp(req.body, "{\"firmware\":\"1.0.0\",\"rssi\":-60}") == 0);
  CHECK(!app.nextRequest(1001, req));  // next one only after a second

  app.onResponse(ClickerApp::RequestKind::Checkin, 200, kUnassigned, 1010);
  CHECK(app.phase() == ClickerApp::Phase::Unassigned);
  CHECK(logged("Waiting for the teacher to assign ESP32-T"));
  CHECK(app.ledColor(1010) == StatusLed::Magenta);
  CHECK(app.ledColor(2020) == StatusLed::Off);  // slow blink

  app.onButton('A', 1500);  // pressing now: magenta x3, nothing sent
  CHECK(app.ledColor(1500) == StatusLed::Magenta);
  CHECK(!app.nextRequest(1500, req));
  CHECK(answerCheckin(app, 2010, 200, kUnassigned));
}

static void test_app_votes() {
  printf("ClickerApp: open question, vote, second press\n");
  gLog.clear();
  ClickerApp app;
  app.begin("ESP32-T", "1.0.0", captureLog, 0);
  app.setWifi(true, 0);
  ClickerApp::Request req;

  CHECK(answerCheckin(app, 0, 200, reply(nullptr, false, false).c_str()));
  CHECK(app.phase() == ClickerApp::Phase::Ready);
  CHECK(!app.armed());
  CHECK(app.ledColor(10) == StatusLed::Green);  // the "I'm on" blip...
  CHECK(app.ledColor(100) == StatusLed::Off);   // ...is short

  app.onButton('B', 50);  // no question yet: red x3 (until 950 ms)
  CHECK(app.ledColor(50) == StatusLed::Red);
  CHECK(logged("no question is open"));

  CHECK(answerCheckin(app, 1000, 200, reply("s_a_r0", true, false).c_str()));
  CHECK(app.armed());
  CHECK(logged("Question open (s_a_r0)"));
  CHECK(app.ledColor(1000) == StatusLed::White);
  CHECK(app.ledColor(1750) == StatusLed::Off);

  app.onButton('C', 2200);
  CHECK(app.ledColor(2200) == StatusLed::Yellow);
  CHECK(app.nextRequest(2200, req));
  CHECK(req.kind == ClickerApp::RequestKind::Vote);
  CHECK(strcmp(req.path, "/api/v1/clicker/vote") == 0);
  CHECK(strcmp(req.body,
               "{\"round_id\":\"s_a_r0\",\"selected_option\":\"C\","
               "\"response_time_ms\":1200}") == 0);
  app.onButton('D', 2210);  // while sending: ignored
  CHECK(!app.nextRequest(2220, req));  // no check-in while the vote is in flight

  app.onResponse(ClickerApp::RequestKind::Vote, 200, "{}", 2230);
  CHECK(logged("Vote C counted"));
  CHECK(app.ledColor(2230) == StatusLed::Green);
  CHECK(app.ledColor(3700) == StatusLed::Green);  // 1.5 s of green
  CHECK(!app.armed());                            // answered locally already

  app.onButton('A', 3800);  // second press in the same round
  CHECK(logged("already answered"));
  CHECK(app.ledColor(3800) == StatusLed::Red);
  // The next check-in confirms the vote on the server: still not armed.
  CHECK(answerCheckin(app, 3800, 200, reply("s_a_r0", true, true).c_str()));
  CHECK(!app.armed());

  // Next question: armed again.
  CHECK(answerCheckin(app, 5000, 200, reply("s_a_r1", true, false).c_str()));
  CHECK(app.armed());
  // The server says this student already answered (e.g. on a phone): not armed.
  CHECK(answerCheckin(app, 6000, 200, reply("s_a_r1", true, true).c_str()));
  CHECK(!app.armed());
}

static void test_app_vote_errors() {
  printf("ClickerApp: 409, retries, lost Wi-Fi, 403\n");
  gLog.clear();
  ClickerApp app;
  app.begin("ESP32-T", "1.0.0", captureLog, 0);
  app.setWifi(true, 0);
  ClickerApp::Request req;
  CHECK(answerCheckin(app, 0, 200, reply("s_b_r0", true, false).c_str()));

  // 409 on the first attempt: red, the round is done for this clicker.
  app.onButton('A', 100);
  CHECK(app.nextRequest(100, req) && req.kind == ClickerApp::RequestKind::Vote);
  app.onResponse(req.kind, 409, "{\"detail\":\"Round is not open.\"}", 120);
  CHECK(logged("not accepted (Round is not open.)"));
  CHECK(app.ledColor(120) == StatusLed::Red);
  CHECK(!app.armed());

  // Network hiccup, then 409 on the retry: the first try did arrive -> counted.
  CHECK(answerCheckin(app, 1000, 200, reply("s_b_r1", true, false).c_str()));
  app.onButton('B', 1100);
  CHECK(app.nextRequest(1100, req));
  app.onResponse(req.kind, -11, "", 1200);  // read timeout
  CHECK(logged("retrying"));
  CHECK(!app.nextRequest(1300, req));  // waits 250 ms, no check-in meanwhile
  CHECK(app.nextRequest(1450, req) && req.kind == ClickerApp::RequestKind::Vote);
  app.onResponse(req.kind, 409, "", 1460);
  CHECK(logged("confirmed on retry"));
  CHECK(app.ledColor(1460) == StatusLed::Green);

  // Three failures in a row: red, and the student may press again.
  CHECK(answerCheckin(app, 2500, 200, reply("s_b_r2", true, false).c_str()));
  app.onButton('C', 2600);
  uint32_t t = 2600;
  for (int i = 0; i < 3; i++) {
    CHECK(app.nextRequest(t, req) && req.kind == ClickerApp::RequestKind::Vote);
    app.onResponse(req.kind, -1, "", t);
    t += 300;
  }
  CHECK(logged("Vote C failed"));
  CHECK(app.armed());

  // Wi-Fi drops with a vote waiting: it is cancelled, never sent late.
  app.onButton('D', 4000);
  app.setWifi(false, 4001);
  CHECK(logged("was NOT sent"));
  CHECK(app.phase() == ClickerApp::Phase::LookingForWifi);
  CHECK(!app.nextRequest(4002, req));
  CHECK(app.ledColor(4002) == StatusLed::Red);

  // Back online; the teacher unassigned the clicker meanwhile: 403 on vote.
  app.setWifi(true, 5000);
  CHECK(answerCheckin(app, 5000, 200, reply("s_b_r2", true, false).c_str()));
  app.onButton('A', 5100);
  CHECK(app.nextRequest(5100, req));
  app.onResponse(req.kind, 403, "{\"detail\":\"Clicker is not assigned\"}", 5110);
  CHECK(app.phase() == ClickerApp::Phase::Unassigned);
  CHECK(app.ledColor(5110) == StatusLed::Magenta);
  CHECK(app.nextRequest(5111, req) && req.kind == ClickerApp::RequestKind::Checkin);
}

static void test_app_server_problems() {
  printf("ClickerApp: server down, refused, old backend\n");
  gLog.clear();
  ClickerApp app;
  app.begin("ESP32-T", "1.0.0", captureLog, 0);
  app.setWifi(true, 0);
  ClickerApp::Request req;

  CHECK(answerCheckin(app, 0, -1, ""));
  CHECK(app.phase() == ClickerApp::Phase::Connecting);
  CHECK(!app.nextRequest(1500, req));  // retries every 2 s
  CHECK(answerCheckin(app, 2000, 502, "bad gateway"));
  CHECK(answerCheckin(app, 4000, -1, ""));
  CHECK(app.phase() == ClickerApp::Phase::ServerUnreachable);
  CHECK(app.ledColor(4000) == StatusLed::Blue && app.ledColor(5100) == StatusLed::Off);
  app.onButton('A', 5200);
  CHECK(logged("not connected yet"));

  CHECK(answerCheckin(app, 6000, 404, "{\"detail\":\"Not Found\"}"));
  CHECK(logged("no clicker API"));
  CHECK(answerCheckin(app, 8000, 200, "garbage"));
  CHECK(logged("not understood"));

  CHECK(answerCheckin(app, 10000, 401, "{\"detail\":\"Clicker not recognized\"}"));
  CHECK(app.phase() == ClickerApp::Phase::Rejected);
  CHECK(logged("removes ESP32-T from the clicker list"));
  CHECK(app.ledColor(10000) == StatusLed::Magenta);
  CHECK(!app.nextRequest(14000, req));  // refused: asks again every 5 s
  CHECK(answerCheckin(app, 15000, 200, kUnassigned));
  CHECK(app.phase() == ClickerApp::Phase::Unassigned);
}

int main() {
  test_buttons();
  test_led();
  test_protocol();
  test_app_connects_and_waits_for_teacher();
  test_app_votes();
  test_app_vote_errors();
  test_app_server_problems();
  printf("\n%d checks, %d failures\n", gChecks, gFailures);
  return gFailures == 0 ? 0 : 1;
}
