#include "LightPlan.h"

namespace light_plan
{

  namespace
  {
    const uint16_t kFastMs = 150;
    const uint16_t kSlowMs = 1000;
    const uint16_t kSteady = 0; // as offMs: never dark

    const StatusLed::Pattern kLookingForWifi = {StatusLed::Blue, kFastMs, kFastMs};
    const StatusLed::Pattern kConnecting = {StatusLed::Blue, 1, kSteady};
    const StatusLed::Pattern kServerUnreachable = {StatusLed::Blue, kSlowMs, kSlowMs};
    const StatusLed::Pattern kRejected = {StatusLed::Magenta, kFastMs, kFastMs};
    const StatusLed::Pattern kUnassigned = {StatusLed::Magenta, kSlowMs, kSlowMs};
    const StatusLed::Pattern kSendingVote = {StatusLed::Yellow, 1, kSteady};
    const StatusLed::Pattern kQuestionOpen = {StatusLed::White, 700, 300};
    const StatusLed::Pattern kIdleBlip = {StatusLed::Green, 60, 2940}; // "I'm on"
  } // namespace

  StatusLed::Pattern backgroundFor(Phase phase, bool votePending, bool questionWaiting)
  {
    switch (phase)
    {
    case Phase::LookingForWifi:
      return kLookingForWifi;
    case Phase::Connecting:
      return kConnecting;
    case Phase::ServerUnreachable:
      return kServerUnreachable;
    case Phase::Rejected:
      return kRejected;
    case Phase::Unassigned:
      return kUnassigned;
    case Phase::Ready:
      break;
    }
    if (votePending)
      return kSendingVote;
    if (questionWaiting)
      return kQuestionOpen;
    return kIdleBlip;
  }

  bool statusLedOn(bool wifiConnected, uint32_t nowMs)
  {
    return wifiConnected || (nowMs / kFastMs) % 2 == 0;
  }

} // namespace light_plan
