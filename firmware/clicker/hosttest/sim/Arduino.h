// PC stand-in for the Arduino-ESP32 core, just enough to run clicker.ino on Linux.
// Signatures follow cores/esp32 (2.0.17 and 3.3.x) so the firmware compiles unchanged.
// This is a test harness, not an emulator: real builds use the ESP32 core.
#pragma once

#include <stdarg.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include <string>

#define LOW 0x0
#define HIGH 0x1
#define INPUT 0x01
#define OUTPUT 0x03
#define INPUT_PULLUP 0x05
#define FALLING 0x02
#define ARDUINO_ISR_ATTR

class String {
 public:
  String() {}
  String(const char* text) : s_(text ? text : "") {}  // NOLINT: implicit like Arduino
  String(const std::string& text) : s_(text) {}       // NOLINT
  const char* c_str() const { return s_.c_str(); }
  unsigned int length() const { return static_cast<unsigned int>(s_.size()); }
  bool operator==(const char* other) const { return s_ == other; }

 private:
  std::string s_;
};

unsigned long millis();
void delay(uint32_t ms);
void pinMode(uint8_t pin, uint8_t mode);
void digitalWrite(uint8_t pin, uint8_t val);
int digitalRead(uint8_t pin);
void attachInterruptArg(uint8_t pin, void (*)(void*), void* arg, int mode);
uint32_t analogReadMilliVolts(uint8_t pin);

class HardwareSerial {
 public:
  void begin(unsigned long baud);
  size_t printf(const char* format, ...) __attribute__((format(printf, 2, 3)));
  size_t println(const char* text);
  size_t println();
};
extern HardwareSerial Serial;

class EspClass {
 public:
  uint64_t getEfuseMac();
  void restart();
};
extern EspClass ESP;
