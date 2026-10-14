// The login half of Connection: when to log in, what each reply means for the
// clicker, and asking again after a refusal. The rest is in Connection.cpp.
#include "Connection.h"

#include "Timing.h"

using protocol::LoginOutcome;

bool Connection::loginIsDue(uint32_t nowMs) const
{
  return !loginRefused_ && nextLogin_.isDue(nowMs);
}

// Replaced when the reply arrives; this covers a reply that never comes.
void Connection::loginSent(uint32_t nowMs)
{
  nextLogin_.dueIn(nowMs, timing::kRetryEveryMs);
}

void Connection::onLoginReply(LoginOutcome outcome, const protocol::LoginReply &reply,
                              int status, const char *detail, uint32_t nowMs)
{
  switch (outcome)
  {
  case LoginOutcome::Accepted:
    token_.assignTruncated(reply.token.c_str());
    failures_ = 0;
    log_.printf("Assigned to %s: ready to vote",
                reply.username.isEmpty() ? "a student" : reply.username.c_str());
    enter(Phase::Ready);
    return;
  case LoginOutcome::Unassigned:
    if (phase_ != Phase::Unassigned)
    {
      log_.printf("Connected, but not assigned. Assign %s to a student in Clickers on "
                  "/maestro/",
                  deviceId_);
    }
    enter(Phase::Unassigned);
    failures_ = 0;
    nextLogin_.dueIn(nowMs, timing::kUnassignedEveryMs);
    return;
  case LoginOutcome::Refused:
    // Enough refused logins lock the clicker out for up to 16 minutes, so there is
    // no timer: a button press asks once more, and so does a restart.
    loginRefused_ = true;
    enter(Phase::Rejected);
    failures_ = 0;
    log_.printf("Utz'tutor refused this clicker's secret (HTTP %d %s)", status, detail);
    log_.printf("Fix: delete %s in Clickers on /maestro/, then press any button",
                deviceId_);
    return;
  case LoginOutcome::LockedOut:
    enter(Phase::Rejected);
    failures_ = 0;
    nextLogin_.dueIn(nowMs, timing::kLockedOutEveryMs);
    log_.printf("Utz'tutor locked this clicker out after refused logins: asking again "
                "in 30 s");
    return;
  case LoginOutcome::NoLoginRoute:
    log_.printf("Utz'tutor has no clicker login (HTTP 404): update the backend");
    break;
  case LoginOutcome::NotUnderstood:
    log_.printf("Login reply was not understood");
    break;
  case LoginOutcome::Failed:
    log_.printf("Login failed (%d %s)", status, detail);
    break;
  }
  nextLogin_.dueIn(nowMs, timing::kRetryEveryMs);
  serverFailed();
}

void Connection::askAgain(uint32_t nowMs)
{
  loginRefused_ = false;
  nextLogin_.dueNow(nowMs);
}

void Connection::endSession(uint32_t nowMs)
{
  token_.wipe();
  startLogin(nowMs);
}

void Connection::startLogin(uint32_t nowMs)
{
  if (loginRefused_)
  {
    enter(Phase::Rejected);
    return;
  }
  log_.printf("Logging in to the Utz'tutor");
  enter(Phase::Connecting);
  nextLogin_.dueNow(nowMs);
}
