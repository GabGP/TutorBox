// Secret, DeviceName and BatteryLevel: the clicker's own facts.
#include <string.h>

#include "check.h"
#include "src/device/BatteryLevel.h"
#include "src/device/DeviceName.h"
#include "src/device/Secret.h"

static void test_secret()
{
  printf("Secret\n");
  CHECK(isSecret("0123456789abcdef0123456789abcdef"));
  CHECK(!isSecret("0123456789ABCDEF0123456789ABCDEF"));  // upper case
  CHECK(!isSecret("0123456789abcdef0123456789abcde"));   // 31
  CHECK(!isSecret("0123456789abcdef0123456789abcdef0")); // 33
  CHECK(!isSecret("0123456789abcdef0123456789abcdeg"));  // not hex
  CHECK(!isSecret(""));
  CHECK(!isSecret(nullptr));

  // Each 32-bit word becomes 8 hex digits, most significant first.
  const uint32_t words[kSecretRandomWords] = {0x01234567u, 0x89abcdefu, 0x00000000u,
                                              0xffffffffu};
  const Secret secret = secretFromRandomWords(words);
  CHECK(strcmp(secret.c_str(), "0123456789abcdef00000000ffffffff") == 0);
  CHECK(isSecret(secret.c_str())); // the shape the server and the store expect
}

static void test_device_name()
{
  printf("DeviceName\n");
  // MAC 24:0A:C4:A4:CF:12, as ESP.getEfuseMac() returns it: byte 0 in the lowest bits.
  const uint64_t efuseMac = 0x12CFA4C40A24ull;
  const DeviceName name = deviceNameFromMac(efuseMac);
  CHECK(strcmp(name.deviceId.c_str(), "ESP32-A4CF12") == 0);
  CHECK(strcmp(name.hostname.c_str(), "clicker-a4cf12") == 0);

  const DeviceName zeros = deviceNameFromMac(0);
  CHECK(strcmp(zeros.deviceId.c_str(), "ESP32-000000") == 0);
}

static void test_battery_level()
{
  printf("BatteryLevel\n");
  CHECK(batteryPercent(3750, 3300, 4200) == 50);
  CHECK(batteryPercent(3300, 3300, 4200) == 0);
  CHECK(batteryPercent(2900, 3300, 4200) == 0);
  CHECK(batteryPercent(4200, 3300, 4200) == 100);
  CHECK(batteryPercent(4350, 3300, 4200) == 100);
  CHECK(batteryPercent(-1, 3300, 4200) == -1);   // not fitted
  CHECK(batteryPercent(3750, 4200, 4200) == -1); // settings make no sense
}

void test_device()
{
  test_secret();
  test_device_name();
  test_battery_level();
}
