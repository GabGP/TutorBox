// The wire format: request bodies and reply parsers.
#include <string.h>

#include "app_fixture.h"
#include "check.h"
#include "src/protocol/Protocol.h"

static void test_request_bodies()
{
  printf("Protocol: request bodies\n");
  char out[protocol::kBodySize];

  protocol::loginBody(out, sizeof(out), "ESP32-A4CF12", kSecret);
  CHECK(strcmp(out,
               "{\"device_id\":\"ESP32-A4CF12\","
               "\"secret\":\"0123456789abcdef0123456789abcdef\"}") == 0);

  protocol::heartbeatBody(out, sizeof(out), -55, 88);
  CHECK(strcmp(out, "{\"rssi\":-55,\"battery_pct\":88}") == 0);
  protocol::heartbeatBody(out, sizeof(out), -55, -1);
  CHECK(strcmp(out, "{\"rssi\":-55}") == 0);
  protocol::heartbeatBody(out, sizeof(out), 0, -1); // Wi-Fi reports 0 when unknown
  CHECK(strcmp(out, "{}") == 0);
  protocol::heartbeatBody(out, sizeof(out), -130, 101); // outside what the API takes
  CHECK(strcmp(out, "{}") == 0);
  protocol::heartbeatBody(out, sizeof(out), -120, 0); // the edges are still taken
  CHECK(strcmp(out, "{\"rssi\":-120,\"battery_pct\":0}") == 0);

  protocol::voteBody(out, sizeof(out), 'C', 1234);
  CHECK(strcmp(out, "{\"selected_option\":\"C\",\"response_time_ms\":1234}") == 0);
  char path[protocol::kPathSize];
  protocol::votePath(path, sizeof(path), "s_a1b2c3d4e5f6");
  CHECK(strcmp(path, "/api/v1/session/s_a1b2c3d4e5f6/vote") == 0);
}

static void test_login_and_detail_parsers()
{
  printf("Protocol: login reply, error detail\n");
  protocol::LoginReply reply;
  CHECK(protocol::parseLogin(kLoggedIn, reply));
  CHECK(reply.token.equals(kToken));
  CHECK(reply.username.equals("ana"));

  protocol::LoginReply refused;
  CHECK(!protocol::parseLogin("not json", refused));
  CHECK(!protocol::parseLogin(kUnassigned, refused));
  // A token that does not fit is refused whole, never cut.
  std::string longToken = "{\"session_id\":\"" + std::string(200, 't') + "\"}";
  CHECK(!protocol::parseLogin(longToken.c_str(), refused));
  CHECK(refused.token.isEmpty());

  CHECK(protocol::detailOf("{\"detail\":\"Round not found.\"}").equals("Round not found."));
  CHECK(protocol::detailOf("{\"detail\":[{\"msg\":\"bad\"}]}").isEmpty()); // a list
  CHECK(protocol::detailOf("").isEmpty());
  CHECK(protocol::detailOf("{}").isEmpty());

  CHECK(protocol::isAlreadyVoted("Student 4 has already voted in round s_x_r0."));
  CHECK(!protocol::isAlreadyVoted("Round 's_x_r0' is not open."));
  CHECK(!protocol::isAlreadyVoted("Voting window has expired."));
  CHECK(!protocol::isAlreadyVoted(""));
  CHECK(!protocol::isAlreadyVoted(nullptr));
}

static void test_session_parser()
{
  printf("Protocol: session reply\n");
  protocol::SessionView view;
  CHECK(protocol::parseSession(session("s_x", "s_x_r0", "open").c_str(), view));
  CHECK(view.roundOpen);
  CHECK(view.sessionId.equals("s_x"));
  CHECK(view.roundId.equals("s_x_r0"));
  CHECK(protocol::parseSession(session("s_x", "s_x_r0", "revealed").c_str(), view));
  CHECK(!view.roundOpen && view.roundId.equals("s_x_r0"));
  CHECK(protocol::parseSession(session("s_x", "s_x_r0", "pending").c_str(), view));
  CHECK(!view.roundOpen); // the lobby: the first question is not open yet
  CHECK(protocol::parseSession(session("s_x", nullptr, "").c_str(), view));
  CHECK(!view.roundOpen && view.roundId.isEmpty());
  CHECK(!protocol::parseSession("not json", view));
  CHECK(!protocol::parseSession(kNoSession, view));
  std::string longRound(200, 'r');
  CHECK(!protocol::parseSession(session("s_x", longRound.c_str(), "open").c_str(), view));
}

void test_protocol()
{
  test_request_bodies();
  test_login_and_detail_parsers();
  test_session_parser();
}
