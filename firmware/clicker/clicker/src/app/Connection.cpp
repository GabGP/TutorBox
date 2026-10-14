#include "Connection.h"

#include "Timing.h"

Connection::Connection(Logger &log)
    : log_(log),
      deviceId_(""),
      phase_(Phase::LookingForWifi),
      wifi_(false),
      loginRefused_(false),
      failures_(0) {}

void Connection::begin(const char *deviceId, const char *secret, uint32_t nowMs)
{
  deviceId_ = deviceId;
  if (isSecret(secret))
    secret_.assignTruncated(secret);
  nextLogin_.dueNow(nowMs);
}

bool Connection::waitingForTeacher() const
{
  return phase_ == Phase::Unassigned || phase_ == Phase::Rejected;
}

Connection::WifiChange Connection::setWifi(bool connected, uint32_t nowMs)
{
  if (connected == wifi_)
    return WifiChange::Unchanged;
  wifi_ = connected;
  if (!connected)
  {
    log_.printf("Wi-Fi lost, reconnecting");
    enter(Phase::LookingForWifi);
    return WifiChange::Lost;
  }
  failures_ = 0;
  if (hasToken())
  {
    log_.printf("Wi-Fi connected again");
    enter(Phase::Ready);
  }
  else
  {
    log_.printf("Wi-Fi connected");
    startLogin(nowMs);
  }
  return WifiChange::Restored;
}

void Connection::serverAnswered()
{
  failures_ = 0;
  if (phase_ != Phase::Ready)
    log_.printf("Utz'tutor answers again");
  enter(Phase::Ready);
}

void Connection::serverFailed()
{
  if (failures_ < 255)
    failures_++;
  if (failures_ >= timing::kFailuresBeforeUnreachable)
    enter(Phase::ServerUnreachable);
}
