#include "Phase.h"

const char *phaseName(Phase phase)
{
  switch (phase)
  {
  case Phase::LookingForWifi:
    return "looking-for-wifi";
  case Phase::Connecting:
    return "connecting";
  case Phase::ServerUnreachable:
    return "server-unreachable";
  case Phase::Rejected:
    return "rejected";
  case Phase::Unassigned:
    return "unassigned";
  case Phase::Ready:
    return "ready";
  }
  return "?";
}
