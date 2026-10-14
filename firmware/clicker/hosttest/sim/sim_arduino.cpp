// Stand-ins for the Arduino core: time, pins, the serial port, the chip itself and its
// random number generator.
#include <chrono>
#include <cstdlib>
#include <random>
#include <thread>

#include "Arduino.h"
#include "esp_random.h"
#include "sim_state.h"

HardwareSerial Serial;
EspClass ESP;

int gLevel[kSimPins];
void (*gIsr[kSimPins])(void *) = {nullptr};
void *gIsrArg[kSimPins] = {nullptr};

namespace
{
  const auto kStart = std::chrono::steady_clock::now();
} // namespace

uint64_t simMac()
{
  const char *text = getenv("CLICKER_SIM_MAC");
  return strtoull(text ? text : "240AC4A4CF12", nullptr, 16);
}

unsigned long millis()
{
  return static_cast<unsigned long>(std::chrono::duration_cast<std::chrono::milliseconds>(
                                        std::chrono::steady_clock::now() - kStart)
                                        .count());
}

// Keeps reading the test's commands while the firmware waits, so a test can release a
// button in the middle of a wait (the reset check waits here).
void delay(uint32_t ms)
{
  const auto until = std::chrono::steady_clock::now() + std::chrono::milliseconds(ms);
  do
  {
    simPumpInput();
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  } while (std::chrono::steady_clock::now() < until);
}

void pinMode(uint8_t pin, uint8_t mode)
{
  (void)pin;
  (void)mode;
}

void digitalWrite(uint8_t pin, uint8_t val) { gLevel[pin] = val ? HIGH : LOW; }

int digitalRead(uint8_t pin) { return gLevel[pin]; }

void attachInterruptArg(uint8_t pin, void (*fn)(void *), void *arg, int mode)
{
  (void)mode;
  gIsr[pin] = fn;
  gIsrArg[pin] = arg;
}

uint32_t analogReadMilliVolts(uint8_t pin)
{
  (void)pin;
  return 1950;
}

// The host's random source: each simulated clicker makes a different secret.
uint32_t esp_random(void)
{
  static std::random_device device;
  return device();
}

void HardwareSerial::begin(unsigned long baud) { (void)baud; }

size_t HardwareSerial::printf(const char *format, ...)
{
  va_list args;
  va_start(args, format);
  const int n = vprintf(format, args);
  va_end(args);
  fflush(stdout);
  return n < 0 ? 0 : static_cast<size_t>(n);
}

size_t HardwareSerial::println(const char *text) { return printf("%s\n", text); }
size_t HardwareSerial::println() { return printf("\n"); }

uint64_t EspClass::getEfuseMac()
{
  // The real call returns MAC byte 0 in the lowest 8 bits.
  const uint64_t mac = simMac();
  uint64_t efuse = 0;
  for (int i = 0; i < 6; i++)
    efuse |= ((mac >> (8 * (5 - i))) & 0xFF) << (8 * i);
  return efuse;
}

void EspClass::restart()
{
  ::printf("SIM restart requested\n");
  fflush(stdout);
  exit(3);
}
