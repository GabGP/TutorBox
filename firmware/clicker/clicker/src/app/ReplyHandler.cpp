#include "ReplyHandler.h"

#include "../protocol/Protocol.h"
#include "../protocol/ReplyMeaning.h"
#include "Timing.h"

using protocol::HeartbeatOutcome;
using protocol::LoginOutcome;
using protocol::PollOutcome;

ReplyHandler::ReplyHandler(Logger &log, Connection &connection, Voting &voting,
                           Schedule &schedule)
    : log_(log), connection_(connection), voting_(voting), schedule_(schedule) {}

void ReplyHandler::handle(RequestKind kind, int status, const char *body,
                          uint32_t nowMs)
{
  switch (kind)
  {
  case RequestKind::Login:
    onLogin(status, body, nowMs);
    break;
  case RequestKind::Poll:
    onPoll(status, body, nowMs);
    break;
  case RequestKind::Heartbeat:
    onHeartbeat(status, body, nowMs);
    break;
  case RequestKind::Vote:
    onVote(status, body, nowMs);
    break;
  case RequestKind::None:
    break;
  }
}

void ReplyHandler::onLogin(int status, const char *body, uint32_t nowMs)
{
  protocol::LoginReply reply;
  const bool understood = status == 200 && protocol::parseLogin(body, reply);
  const LoginOutcome outcome = protocol::loginOutcome(status, understood);
  if (outcome == LoginOutcome::Accepted)
  {
    connection_.onLoginReply(outcome, reply, status, "", nowMs);
    schedule_.pollAndBeatNow(nowMs);
    return;
  }
  // No token. A vote that was waiting for one is dropped and shown, never sent late.
  const bool teacher = protocol::needsTeacher(outcome);
  voting_.dropForNoSession(teacher ? StatusLed::Magenta : StatusLed::Red, nowMs);
  connection_.onLoginReply(outcome, reply, status, protocol::detailOf(body).c_str(),
                           nowMs);
}

void ReplyHandler::onPoll(int status, const char *body, uint32_t nowMs)
{
  protocol::SessionView view;
  const bool understood = status == 200 && protocol::parseSession(body, view);
  const PollOutcome outcome = protocol::pollOutcome(status, understood);
  if (outcome == PollOutcome::MatchRunning || outcome == PollOutcome::NoMatch)
  {
    schedule_.nextPoll.dueIn(nowMs, timing::kPollEveryMs);
    connection_.serverAnswered();
    if (outcome == PollOutcome::MatchRunning)
    {
      voting_.followMatch(view, nowMs);
    }
    else
    {
      voting_.forgetOpenRound();
    }
    return;
  }
  schedule_.nextPoll.dueIn(nowMs, timing::kRetryEveryMs);
  if (outcome == PollOutcome::NotUnderstood)
  {
    log_.printf("Session reply was not understood");
  }
  else
  {
    log_.printf("Utz'tutor did not answer (%d)", status);
  }
  connection_.serverFailed();
}

void ReplyHandler::onHeartbeat(int status, const char *body, uint32_t nowMs)
{
  switch (protocol::heartbeatOutcome(status))
  {
  case HeartbeatOutcome::SessionEnded:
    log_.printf("Utz'tutor ended this clicker's session: logging in again");
    endSession(nowMs);
    return;
  case HeartbeatOutcome::Refused:
    log_.printf("Heartbeat refused (HTTP %d %s)", status,
                protocol::detailOf(body).c_str());
    return;
  case HeartbeatOutcome::Delivered:
  case HeartbeatOutcome::NoAnswer: // the poll, sent five times as often, reports that
    return;
  }
}

void ReplyHandler::onVote(int status, const char *body, uint32_t nowMs)
{
  switch (voting_.onVoteReply(status, body, nowMs))
  {
  case Voting::Next::RefreshRound:
    schedule_.nextPoll.dueIn(nowMs, timing::kRefreshAfterVoteMs);
    return;
  case Voting::Next::LogInAgain:
    endSession(nowMs);
    return;
  case Voting::Next::Nothing:
    return;
  }
}

// The token is no longer valid: what the clicker knew about the round goes with it.
void ReplyHandler::endSession(uint32_t nowMs)
{
  connection_.endSession(nowMs);
  voting_.forgetOpenRound();
}
