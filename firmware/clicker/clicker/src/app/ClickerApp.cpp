#include "ClickerApp.h"

#include "LightPlan.h"
#include "Timing.h"

ClickerApp::ClickerApp()
    : connection_(log_),
      voting_(log_, led_),
      replies_(log_, connection_, voting_, schedule_),
      inFlight_(false),
      rssi_(0),
      batteryPct_(-1) {}

void ClickerApp::begin(const char *deviceId, const char *firmware, const char *secret,
                       Logger::Sink log, uint32_t nowMs)
{
  log_.setSink(log);
  connection_.begin(deviceId, secret, nowMs);
  log_.printf("Clicker %s, firmware %s: looking for Wi-Fi", deviceId, firmware);
}

// ---- what happened -----------------------------------------------------------

void ClickerApp::setWifi(bool connected, uint32_t nowMs)
{
  switch (connection_.setWifi(connected, nowMs))
  {
  case Connection::WifiChange::Lost:
    inFlight_ = false; // its reply will never come
    voting_.forgetOpenRound();
    voting_.dropForNoWifi(nowMs);
    break;
  case Connection::WifiChange::Restored:
    if (connection_.hasToken())
      schedule_.pollAndBeatNow(nowMs);
    break;
  case Connection::WifiChange::Unchanged:
    break;
  }
}

void ClickerApp::setVitals(int rssi, int batteryPct)
{
  rssi_ = rssi;
  batteryPct_ = batteryPct;
}

void ClickerApp::onButton(char option, uint32_t nowMs)
{
  if (voting_.isSending())
    return; // one vote in flight at a time
  if (connection_.phase() == Phase::Ready)
  {
    voting_.press(option, nowMs);
  }
  else
  {
    onButtonWhileNotReady(option, nowMs);
  }
}

void ClickerApp::onResponse(RequestKind kind, int status, const char *body,
                            uint32_t nowMs)
{
  inFlight_ = false;
  replies_.handle(kind, status, body, nowMs);
}

// ---- what to do --------------------------------------------------------------

// First the login (nothing works without a token), then the vote (a student is
// waiting for the light), then the heartbeat, then the poll.
bool ClickerApp::nextRequest(uint32_t nowMs, Request &out)
{
  if (!connection_.wifiUp() || inFlight_)
    return false;
  if (!connection_.hasToken())
  {
    if (!connection_.loginIsDue(nowMs))
      return false;
    makeLoginRequest(out, connection_.deviceId(), connection_.secret());
    connection_.loginSent(nowMs);
  }
  else if (voting_.isSending())
  {
    if (!voting_.tryIsDue(nowMs))
      return false; // between two tries of a vote
    voting_.makeRequest(out, connection_.token());
  }
  else if (schedule_.nextHeartbeat.isDue(nowMs))
  {
    makeHeartbeatRequest(out, connection_.token(), rssi_, batteryPct_);
    schedule_.nextHeartbeat.dueIn(nowMs, timing::kHeartbeatEveryMs);
  }
  else if (schedule_.nextPoll.isDue(nowMs))
  {
    makePollRequest(out);
    schedule_.nextPoll.dueIn(nowMs, timing::kPollEveryMs); // replaced by the reply
  }
  else
  {
    return false;
  }
  inFlight_ = true;
  return true;
}

StatusLed::Color ClickerApp::ledColor(uint32_t nowMs)
{
  led_.setPattern(light_plan::backgroundFor(phase(), voting_.isSending(), armed()),
                  nowMs);
  return led_.colorAt(nowMs);
}

bool ClickerApp::statusLedOn(uint32_t nowMs) const
{
  return light_plan::statusLedOn(connection_.wifiUp(), nowMs);
}

bool ClickerApp::armed() const
{
  return phase() == Phase::Ready && voting_.waitingForAnswer();
}

// ---- helpers -----------------------------------------------------------------

// Nothing is sent. Magenta when only the teacher can help, red otherwise. A press is
// also the only thing that asks a refused clicker again (Connection::askAgain).
void ClickerApp::onButtonWhileNotReady(char option, uint32_t nowMs)
{
  const bool teacher = connection_.waitingForTeacher();
  led_.blink(teacher ? StatusLed::Magenta : StatusLed::Red, light_plan::kNoBlinks, nowMs);
  if (connection_.phase() == Phase::Rejected)
  {
    connection_.askAgain(nowMs);
    log_.printf("Button %c: asking the Utz'tutor again", option);
    return;
  }
  log_.printf("Button %c ignored: %s", option,
              teacher ? "this clicker needs the teacher (see README)"
                      : "not connected yet");
}
