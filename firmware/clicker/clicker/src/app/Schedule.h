// When the next poll and the next heartbeat are due. ClickerApp sends them when due;
// ReplyHandler moves them when replies arrive.
#pragma once

#include <stdint.h>

#include "../support/Deadline.h"

struct Schedule
{
  Deadline nextPoll;
  Deadline nextHeartbeat;

  // After a login, or Wi-Fi back: the teacher's lobby shows the clicker at once.
  void pollAndBeatNow(uint32_t nowMs)
  {
    nextPoll.dueNow(nowMs);
    nextHeartbeat.dueNow(nowMs);
  }
};
