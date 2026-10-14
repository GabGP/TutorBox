// The Wi-Fi radio: joins the classroom network from secrets.h and keeps it joined.
#pragma once

#include <stdint.h>

class WifiLink
{
public:
  // Starts the radio. The router lists the clicker under `hostname`.
  void start(const char *hostname);

  // Call every loop. Re-joins after 20 s offline, restarts the clicker after 3 minutes.
  void maintain(uint32_t nowMs);

  bool connected() const;
  // Signal strength in dBm; 0 while not connected.
  int rssi() const;

private:
  uint32_t offlineSinceMs_ = 0;
  uint32_t lastJoinAttemptMs_ = 0;
  bool txPowerSet_ = false;
};
