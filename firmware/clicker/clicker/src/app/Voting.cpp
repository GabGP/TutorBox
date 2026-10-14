#include "Voting.h"

#include "../protocol/ReplyMeaning.h"
#include "LightPlan.h"
#include "Timing.h"

using protocol::VoteOutcome;

Voting::Voting(Logger &log, StatusLed &led) : log_(log), led_(led) {}

bool Voting::waitingForAnswer() const
{
  return !vote_.isPending() && rounds_.waitingForAnswer();
}

void Voting::followMatch(const protocol::SessionView &view, uint32_t nowMs)
{
  rounds_.follow(view);
  if (waitingForAnswer() && !rounds_.noticed())
  {
    rounds_.notice(nowMs);
    log_.printf("Question open (%s): press A, B, C or D", rounds_.roundId());
  }
}

void Voting::press(char option, uint32_t nowMs)
{
  if (!waitingForAnswer())
  {
    led_.blink(StatusLed::Red, light_plan::kNoBlinks, nowMs);
    log_.printf("Button %c ignored: %s", option,
                rounds_.isOpen() ? "this question is already answered"
                                 : "no question is open");
    return;
  }
  vote_.start(option, rounds_.sessionId(), rounds_.roundId(),
              rounds_.msSinceNoticed(nowMs), nowMs);
  log_.printf("Button %c: sending vote for %s", option, vote_.roundId());
}

void Voting::makeRequest(Request &out, const char *token)
{
  makeVoteRequest(out, token, vote_.sessionId(), vote_.option(), vote_.responseMs());
  vote_.countTry();
}

Voting::Next Voting::onVoteReply(int status, const char *body, uint32_t nowMs)
{
  const protocol::ErrorDetail detail = protocol::detailOf(body);
  const char option = vote_.option();
  switch (protocol::voteOutcome(status, vote_.attempts(), timing::kVoteAttempts,
                                detail.c_str()))
  {
  case VoteOutcome::Counted:
    finish(true, nowMs);
    log_.printf("Vote %c counted", option);
    return Next::RefreshRound;
  case VoteOutcome::CountedOnRetry:
    finish(true, nowMs);
    log_.printf("Vote %c counted (confirmed on retry)", option);
    return Next::RefreshRound;
  case VoteOutcome::NotAccepted:
    finish(false, nowMs);
    log_.printf("Vote %c not accepted (%s)", option, detail.c_str());
    return Next::RefreshRound;
  case VoteOutcome::SessionEnded:
    // The vote stays pending: the clicker logs in, then sends it.
    if (vote_.attempts() >= timing::kVoteAttempts)
      drop(StatusLed::Red, nowMs);
    log_.printf("Vote %c: the session ended, logging in again", option);
    return Next::LogInAgain;
  case VoteOutcome::RetrySoon:
    vote_.retryIn(nowMs, timing::kVoteRetryMs); // a network hiccup: same vote again
    log_.printf("Vote %c: no answer (%d), retrying", option, status);
    return Next::Nothing;
  case VoteOutcome::Failed:
    break;
  }
  drop(StatusLed::Red, nowMs);
  log_.printf("Vote %c failed (HTTP %d %s). Press again while the light is white.",
              option, status, detail.c_str());
  return Next::Nothing;
}

void Voting::dropForNoWifi(uint32_t nowMs)
{
  if (!vote_.isPending())
    return;
  drop(StatusLed::Red, nowMs);
  log_.printf("Vote %c was NOT sent (no Wi-Fi). Press again when the light is white.",
              vote_.option());
}

void Voting::dropForNoSession(StatusLed::Color color, uint32_t nowMs)
{
  if (!vote_.isPending())
    return;
  drop(color, nowMs);
  log_.printf("Vote %c was NOT sent (no session)", vote_.option());
}

// The round is done either way: the clicker never votes twice in it.
void Voting::finish(bool counted, uint32_t nowMs)
{
  vote_.clear();
  rounds_.markAnswered(vote_.roundId());
  if (counted)
  {
    led_.flash(StatusLed::Green, light_plan::kCountedFlashMs, nowMs);
  }
  else
  {
    led_.blink(StatusLed::Red, light_plan::kNoBlinks, nowMs);
  }
}

void Voting::drop(StatusLed::Color color, uint32_t nowMs)
{
  vote_.clear();
  led_.blink(color, light_plan::kNoBlinks, nowMs);
}
