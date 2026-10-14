// Runs the real clicker firmware (clicker.ino and its sources) on a PC.
//
// Pins, Wi-Fi and flash are simulated; HTTP is real, so the clicker talks to an actual
// Utz'tutor backend. Driven by text commands on stdin, one per line:
//   press A | tap A | hold A | release A | wifi off | wifi on | quit
// It prints the firmware's serial log plus "LED <color>" whenever the RGB LED changes.
// Commands are read while the firmware runs and also while it waits in delay() (its
// reset check waits there), so a test can release a button in the middle of that wait.
//
// Environment:
//   CLICKER_SIM_SERVER  host:port to send HTTP to instead of UTZTUTOR_URL's host
//   CLICKER_SIM_MAC     12 hex digits (default 240AC4A4CF12 -> ESP32-A4CF12)
//   CLICKER_SIM_NVS     file standing in for flash (default build/nvs-<mac>.txt)
//   CLICKER_SIM_HELD    buttons held down from power-on, e.g. "AD" (default: none)
//
// The stand-ins: sim_arduino.cpp (core), sim_wifi.cpp, sim_http.cpp, sim_preferences.cpp.
#include <poll.h>
#include <unistd.h>

#include <cstdlib>
#include <sstream>
#include <string>
#include <vector>

#include "Arduino.h"
#include "WiFi.h"
#include "config.h"
#include "sim_state.h"

void setup();
void loop();

namespace
{

  std::string gPendingInput; // stdin bytes not yet split into lines
  struct Release
  {
    int pin;
    unsigned long at;
  };
  std::vector<Release> gReleases; // presses that end by themselves: "press" is 120 ms
  std::string gLastColor = "Off";

  int pinFor(char option)
  {
    switch (option)
    {
    case 'A':
      return PIN_BUTTON_A;
    case 'B':
      return PIN_BUTTON_B;
    case 'C':
      return PIN_BUTTON_C;
    case 'D':
      return PIN_BUTTON_D;
    }
    return -1;
  }

  void firePressEdge(int pin)
  {
    gLevel[pin] = LOW;
    if (gIsr[pin] != nullptr)
      gIsr[pin](gIsrArg[pin]);
  }

  const char *colorName(int red, int green, int blue)
  {
    static const char *names[8] = {"Off", "Red", "Green", "Yellow",
                                   "Blue", "Magenta", "Cyan", "White"};
    const int on = LED_COMMON_ANODE ? LOW : HIGH;
    const int bits = (red == on ? 1 : 0) | (green == on ? 2 : 0) | (blue == on ? 4 : 0);
    return names[bits];
  }

  void reportLed()
  {
    const std::string color = colorName(gLevel[PIN_LED_RED], gLevel[PIN_LED_GREEN],
                                        gLevel[PIN_LED_BLUE]);
    if (color != gLastColor)
    {
      gLastColor = color;
      ::printf("LED %s\n", color.c_str());
    }
  }

  void runCommand(const std::string &line)
  {
    std::istringstream words(line);
    std::string verb, arg;
    words >> verb >> arg;
    const int pin = arg.empty() ? -1 : pinFor(arg[0]);
    ::printf("SIM < %s\n", line.c_str());
    if (verb == "quit")
    {
      fflush(stdout);
      exit(0);
    }
    else if (verb == "wifi")
    {
      simSetWifi(arg == "on");
    }
    else if (pin >= 0 && verb == "press")
    {
      firePressEdge(pin); // a normal press: down for 120 ms
      Release release = {pin, millis() + 120};
      gReleases.push_back(release);
    }
    else if (pin >= 0 && verb == "tap")
    {
      firePressEdge(pin); // so short that loop() never sees the pin LOW
      gLevel[pin] = HIGH;
    }
    else if (pin >= 0 && verb == "hold")
    {
      firePressEdge(pin);
    }
    else if (pin >= 0 && verb == "release")
    {
      gLevel[pin] = HIGH;
    }
  }

  void endTimedPresses()
  {
    for (size_t i = 0; i < gReleases.size();)
    {
      if (millis() >= gReleases[i].at)
      {
        gLevel[gReleases[i].pin] = HIGH;
        gReleases.erase(gReleases.begin() + static_cast<long>(i));
      }
      else
      {
        i++;
      }
    }
  }

} // namespace

void simPumpInput()
{
  pollfd input;
  input.fd = 0;
  input.events = POLLIN;
  if (poll(&input, 1, 0) > 0)
  {
    char chunk[256];
    const ssize_t n = read(0, chunk, sizeof(chunk));
    if (n <= 0)
      exit(0); // the test closed our stdin: the clicker is switched off
    gPendingInput.append(chunk, static_cast<size_t>(n));
  }
  size_t newline;
  while ((newline = gPendingInput.find('\n')) != std::string::npos)
  {
    const std::string line = gPendingInput.substr(0, newline);
    gPendingInput.erase(0, newline + 1);
    runCommand(line);
  }
  endTimedPresses();
  reportLed();
}

int main()
{
  setvbuf(stdout, nullptr, _IOLBF, 0);
  for (int i = 0; i < kSimPins; i++)
    gLevel[i] = HIGH; // buttons up
  // The LED starts dark: a common cathode is dark when LOW, a common anode when HIGH.
  gLevel[PIN_LED_RED] = gLevel[PIN_LED_GREEN] = gLevel[PIN_LED_BLUE] =
      LED_COMMON_ANODE ? HIGH : LOW;
  // CLICKER_SIM_HELD=AD: those buttons are down from power-on (the reset gesture test).
  const char *held = getenv("CLICKER_SIM_HELD");
  for (const char *letter = held ? held : ""; *letter != '\0'; letter++)
  {
    const int pin = pinFor(*letter);
    if (pin >= 0)
      gLevel[pin] = LOW;
  }
  setup();
  for (;;)
  {
    simPumpInput();
    loop();
  }
  return 0;
}
