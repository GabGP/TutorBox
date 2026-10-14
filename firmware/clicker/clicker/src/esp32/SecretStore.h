// Keeps the clicker's secret in flash (NVS). The clicker makes it once, so every later
// boot logs in with the same one. The secret is printed nowhere.
#pragma once

#include "../device/Secret.h"

class SecretStore
{
public:
  // Reads the secret from flash, or makes one the first time (a restart keeps it).
  // Call after WifiLink::start(): esp_random() is only truly random while the radio
  // is on.
  void loadOrCreate();

  // Erases the stored secret: the next loadOrCreate() makes a new one. False if flash
  // refused the erase, and then the old secret is kept.
  bool forget();

  // 32 hex characters; "" until loadOrCreate() has run.
  const char *secret() const { return secret_.c_str(); }

private:
  Secret secret_;
};
