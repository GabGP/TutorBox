#include "ReplyMeaning.h"

#include "Protocol.h"

namespace protocol
{

  namespace
  {
    const int kOk = 200;
    const int kUnauthorized = 401;
    const int kForbidden = 403;
    const int kNotFound = 404;
    const int kConflict = 409;
    const int kUnprocessable = 422;
    const int kTooManyRequests = 429;

    bool isClientError(int status) { return status >= 400 && status < 500; }
    bool noAnswer(int status) { return status < 0 || status >= 500; }
  } // namespace

  LoginOutcome loginOutcome(int status, bool replyUnderstood)
  {
    if (status == kOk)
    {
      return replyUnderstood ? LoginOutcome::Accepted : LoginOutcome::NotUnderstood;
    }
    if (status == kForbidden)
      return LoginOutcome::Unassigned;
    if (status == kUnauthorized || status == kUnprocessable)
      return LoginOutcome::Refused;
    if (status == kTooManyRequests)
      return LoginOutcome::LockedOut;
    if (status == kNotFound)
      return LoginOutcome::NoLoginRoute;
    return LoginOutcome::Failed;
  }

  bool needsTeacher(LoginOutcome outcome)
  {
    return outcome == LoginOutcome::Unassigned || outcome == LoginOutcome::Refused ||
           outcome == LoginOutcome::LockedOut;
  }

  PollOutcome pollOutcome(int status, bool replyUnderstood)
  {
    if (status == kOk)
    {
      return replyUnderstood ? PollOutcome::MatchRunning : PollOutcome::NotUnderstood;
    }
    if (status == kNotFound)
      return PollOutcome::NoMatch;
    return PollOutcome::Failed;
  }

  HeartbeatOutcome heartbeatOutcome(int status)
  {
    if (status == kUnauthorized)
      return HeartbeatOutcome::SessionEnded;
    if (isClientError(status))
      return HeartbeatOutcome::Refused;
    if (noAnswer(status))
      return HeartbeatOutcome::NoAnswer;
    return HeartbeatOutcome::Delivered;
  }

  VoteOutcome voteOutcome(int status, uint8_t attemptsSoFar, uint8_t maxAttempts,
                          const char *detail)
  {
    if (status == kOk)
      return VoteOutcome::Counted;
    if (status == kConflict || status == kNotFound)
    {
      // "Already voted" on a retry means the first try did arrive. Any other refusal
      // (the round closed, the match ended) is not a confirmation.
      const bool confirmedByRetry =
          status == kConflict && attemptsSoFar > 1 && isAlreadyVoted(detail);
      return confirmedByRetry ? VoteOutcome::CountedOnRetry : VoteOutcome::NotAccepted;
    }
    if (status == kUnauthorized)
      return VoteOutcome::SessionEnded;
    if (noAnswer(status) && attemptsSoFar < maxAttempts)
      return VoteOutcome::RetrySoon;
    return VoteOutcome::Failed;
  }

} // namespace protocol
