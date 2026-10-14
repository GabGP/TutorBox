// Unit tests for the clicker's pure logic (no ESP32 needed): ../run_tests.sh
#include "check.h"

int gChecks = 0;
int gFailures = 0;
std::vector<std::string> gLog;

void captureLog(const char *line) { gLog.push_back(line); }

bool logged(const char *fragment)
{
  for (size_t i = 0; i < gLog.size(); i++)
  {
    if (gLog[i].find(fragment) != std::string::npos)
      return true;
  }
  return false;
}

// One function per test file, in the order the code is layered.
void test_support();
void test_device();
void test_input();
void test_light();
void test_protocol();
void test_reply_meaning();
void test_app_parts();
void test_app_login();
void test_app_voting();
void test_app_vote_errors();
void test_app_session();

int main()
{
  test_support();
  test_device();
  test_input();
  test_light();
  test_protocol();
  test_reply_meaning();
  test_app_parts();
  test_app_login();
  test_app_voting();
  test_app_vote_errors();
  test_app_session();
  printf("\n%d checks, %d failures\n", gChecks, gFailures);
  return gFailures == 0 ? 0 : 1;
}
