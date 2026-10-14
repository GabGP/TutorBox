#include "SecretStore.h"

#include <Arduino.h>
#include <Preferences.h>

#if __has_include(<esp_random.h>)
#include <esp_random.h> // Arduino-ESP32 3.x (2.0.x has it too, through esp_system.h)
#else
#include <esp_system.h> // Arduino-ESP32 2.0.x builds without esp_random.h
#endif

namespace
{

  const char kNamespace[] = "clicker";
  const char kSecretKey[] = "secret";

  // 128 bits from the hardware random number generator.
  Secret makeSecret()
  {
    uint32_t words[kSecretRandomWords];
    for (size_t i = 0; i < kSecretRandomWords; i++)
      words[i] = esp_random();
    return secretFromRandomWords(words);
  }

} // namespace

void SecretStore::loadOrCreate()
{
  Preferences prefs;
  prefs.begin(kNamespace, false);
  const String saved = prefs.isKey(kSecretKey) ? prefs.getString(kSecretKey) : String();
  if (isSecret(saved.c_str()))
  {
    prefs.end();
    secret_.assignTruncated(saved.c_str());
    Serial.println("[clicker] secret found in flash");
    return;
  }

  secret_ = makeSecret();
  const size_t written = prefs.putString(kSecretKey, secret_.c_str());
  const bool kept = written == strlen(secret_.c_str());
  prefs.end();
  if (kept)
  {
    Serial.println("[clicker] first boot: created this clicker's secret");
  }
  else
  {
    // The secret works until power-off. After that the clicker makes another one, and
    // the Utz'tutor refuses it: see the README, troubleshooting.
    Serial.println(
        "[clicker] first boot: created this clicker's secret, but flash did not keep "
        "it: it will not survive power-off");
  }
}

bool SecretStore::forget()
{
  Preferences prefs;
  prefs.begin(kNamespace, false);
  // A key that is not there has nothing to erase.
  const bool erased = !prefs.isKey(kSecretKey) || prefs.remove(kSecretKey);
  prefs.end();
  secret_.wipe(); // loadOrCreate() makes the new one after the radio starts
  return erased;
}
