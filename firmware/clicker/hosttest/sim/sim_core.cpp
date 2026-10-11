// Runs the real clicker firmware (clicker.ino + Board.cpp + logic) on a PC.
//
// Pins, Wi-Fi and flash are simulated; HTTP is real, so the clicker talks to an actual
// TutorBox backend. Driven by text commands on stdin, one per line:
//   press A | tap A | hold A | release A | wifi off | wifi on | quit
// It prints the firmware's serial log plus "LED <color>" whenever the RGB LED changes.
//
// Environment:
//   CLICKER_SIM_SERVER  host:port to send HTTP to instead of TUTORBOX_URL's host
//   CLICKER_SIM_MAC     12 hex digits (default 240AC4A4CF12 -> ESP32-A4CF12)
//   CLICKER_SIM_NVS     file standing in for flash (default build/nvs-<mac>.txt)
#include <arpa/inet.h>
#include <netdb.h>
#include <poll.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>

#include <chrono>
#include <cerrno>
#include <cstdlib>
#include <fstream>
#include <map>
#include <random>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

#include "Arduino.h"
#include "HTTPClient.h"
#include "Preferences.h"
#include "WiFi.h"
#include "config.h"
#include "esp_system.h"

HardwareSerial Serial;
EspClass ESP;
WiFiClass WiFi;

void setup();
void loop();

namespace {

const auto kStart = std::chrono::steady_clock::now();
int gLevel[32];
uint8_t gMode[32];
void (*gIsr[32])(void*) = {nullptr};
void* gIsrArg[32] = {nullptr};
bool gWifiWanted = true;  // the simulated access point is reachable
bool gWifiStarted = false;
bool gWifiUp = false;
unsigned long gWifiUpAt = 0;
std::vector<WiFiEventFuncCb> gWifiHandlers;

uint64_t simMac() {
  const char* text = getenv("CLICKER_SIM_MAC");
  return strtoull(text ? text : "240AC4A4CF12", nullptr, 16);
}

int pinFor(char option) {
  switch (option) {
    case 'A': return PIN_BUTTON_A;
    case 'B': return PIN_BUTTON_B;
    case 'C': return PIN_BUTTON_C;
    case 'D': return PIN_BUTTON_D;
  }
  return -1;
}

void firePressEdge(int pin) {
  gLevel[pin] = LOW;
  if (gIsr[pin] != nullptr) gIsr[pin](gIsrArg[pin]);
}

void notifyWifi(arduino_event_id_t event, uint8_t reason) {
  arduino_event_info_t info;
  info.wifi_sta_disconnected.reason = reason;
  for (size_t i = 0; i < gWifiHandlers.size(); i++) gWifiHandlers[i](event, info);
}

void updateWifi() {
  const bool up = gWifiStarted && gWifiWanted && millis() >= gWifiUpAt;
  if (up == gWifiUp) return;
  gWifiUp = up;
  notifyWifi(up ? ARDUINO_EVENT_WIFI_STA_GOT_IP : ARDUINO_EVENT_WIFI_STA_DISCONNECTED,
             up ? 0 : WIFI_REASON_NO_AP_FOUND);
}

}  // namespace

// ---------------------------------------------------------------------------
// Arduino core
// ---------------------------------------------------------------------------

unsigned long millis() {
  return static_cast<unsigned long>(std::chrono::duration_cast<std::chrono::milliseconds>(
                                        std::chrono::steady_clock::now() - kStart)
                                        .count());
}

void delay(uint32_t ms) { std::this_thread::sleep_for(std::chrono::milliseconds(ms)); }

void pinMode(uint8_t pin, uint8_t mode) {
  gMode[pin] = mode;
  if (mode == INPUT_PULLUP) gLevel[pin] = HIGH;
}

void digitalWrite(uint8_t pin, uint8_t val) { gLevel[pin] = val ? HIGH : LOW; }

int digitalRead(uint8_t pin) { return gLevel[pin]; }

void attachInterruptArg(uint8_t pin, void (*fn)(void*), void* arg, int mode) {
  (void)mode;
  gIsr[pin] = fn;
  gIsrArg[pin] = arg;
}

uint32_t analogReadMilliVolts(uint8_t pin) {
  (void)pin;
  return 1950;
}

uint32_t esp_random(void) {
  static std::random_device device;
  return device();
}

void HardwareSerial::begin(unsigned long baud) { (void)baud; }

size_t HardwareSerial::printf(const char* format, ...) {
  va_list args;
  va_start(args, format);
  const int n = vprintf(format, args);
  va_end(args);
  fflush(stdout);
  return n < 0 ? 0 : static_cast<size_t>(n);
}

size_t HardwareSerial::println(const char* text) { return printf("%s\n", text); }
size_t HardwareSerial::println() { return printf("\n"); }

uint64_t EspClass::getEfuseMac() {
  // The real call returns MAC byte 0 in the lowest 8 bits.
  const uint64_t mac = simMac();
  uint64_t efuse = 0;
  for (int i = 0; i < 6; i++) efuse |= ((mac >> (8 * (5 - i))) & 0xFF) << (8 * i);
  return efuse;
}

void EspClass::restart() {
  ::printf("SIM restart requested\n");
  fflush(stdout);
  exit(3);
}

// ---------------------------------------------------------------------------
// WiFi
// ---------------------------------------------------------------------------

void WiFiClass::persistent(bool persistent) { (void)persistent; }
bool WiFiClass::setHostname(const char* hostname) {
  ::printf("SIM hostname %s\n", hostname);
  return true;
}
bool WiFiClass::mode(wifi_mode_t mode) { return mode == WIFI_STA; }
bool WiFiClass::setAutoReconnect(bool autoReconnect) { return autoReconnect; }
bool WiFiClass::setSleep(bool enabled) {
  (void)enabled;
  return true;
}
int WiFiClass::onEvent(WiFiEventFuncCb cbEvent, arduino_event_id_t event) {
  (void)event;
  gWifiHandlers.push_back(cbEvent);
  return static_cast<int>(gWifiHandlers.size());
}
wl_status_t WiFiClass::begin(const char* ssid, const char* passphrase, int32_t channel,
                             const uint8_t* bssid, bool connect) {
  (void)ssid;
  (void)passphrase;
  (void)channel;
  (void)bssid;
  (void)connect;
  gWifiStarted = true;
  gWifiUpAt = millis() + 300;  // association + DHCP take a moment
  return WL_DISCONNECTED;
}
bool WiFiClass::setTxPower(wifi_power_t power) {
  ::printf("SIM tx power %d\n", static_cast<int>(power));
  return gWifiStarted;
}
bool WiFiClass::disconnect(bool wifioff, bool eraseap) {
  (void)wifioff;
  (void)eraseap;
  return true;
}
wl_status_t WiFiClass::status() {
  updateWifi();
  return gWifiUp ? WL_CONNECTED : WL_DISCONNECTED;
}
int8_t WiFiClass::RSSI() { return gWifiUp ? -58 : 0; }
IPAddress WiFiClass::localIP() { return IPAddress(); }
const char* WiFiClass::disconnectReasonName(wifi_err_reason_t reason) {
  return reason == WIFI_REASON_NO_AP_FOUND ? "NO_AP_FOUND" : "UNSPECIFIED";
}

void simSetWifi(bool up) {
  gWifiWanted = up;
  if (up) gWifiUpAt = millis() + 300;
}

// ---------------------------------------------------------------------------
// HTTPClient: real HTTP/1.1, one request per connection
// ---------------------------------------------------------------------------

bool HTTPClient::begin(WiFiClient& client, String url) {
  (void)client;
  std::string text = url.c_str();
  const std::string scheme = "http://";
  if (text.compare(0, scheme.size(), scheme) != 0) return false;
  text = text.substr(scheme.size());
  const size_t slash = text.find('/');
  std::string hostPort = text.substr(0, slash);
  path_ = slash == std::string::npos ? "/" : text.substr(slash);
  const char* override = getenv("CLICKER_SIM_SERVER");
  if (override != nullptr) hostPort = override;
  const size_t colon = hostPort.find(':');
  host_ = hostPort.substr(0, colon);
  port_ = colon == std::string::npos ? 80 : atoi(hostPort.c_str() + colon + 1);
  headers_.clear();
  body_.clear();
  return true;
}

void HTTPClient::end(void) { headers_.clear(); }
void HTTPClient::setReuse(bool reuse) { (void)reuse; }
void HTTPClient::setConnectTimeout(int32_t connectTimeout) { (void)connectTimeout; }
void HTTPClient::setTimeout(uint16_t timeout) { timeoutMs_ = timeout; }

void HTTPClient::addHeader(const String& name, const String& value, bool first,
                           bool replace) {
  (void)first;
  (void)replace;
  headers_.push_back(std::string(name.c_str()) + ": " + value.c_str());
}

int HTTPClient::POST(uint8_t* payload, size_t size) {
  body_.clear();
  if (!gWifiUp) return HTTPC_ERROR_NOT_CONNECTED;
  addrinfo hints;
  memset(&hints, 0, sizeof(hints));
  hints.ai_family = AF_INET;
  hints.ai_socktype = SOCK_STREAM;
  addrinfo* found = nullptr;
  if (getaddrinfo(host_.c_str(), std::to_string(port_).c_str(), &hints, &found) != 0) {
    return HTTPC_ERROR_CONNECTION_REFUSED;
  }
  const int fd = socket(found->ai_family, found->ai_socktype, found->ai_protocol);
  timeval tv;
  tv.tv_sec = timeoutMs_ / 1000;
  tv.tv_usec = (timeoutMs_ % 1000) * 1000;
  setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
  setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));
  const int connected = connect(fd, found->ai_addr, found->ai_addrlen);
  freeaddrinfo(found);
  if (connected != 0) {
    close(fd);
    return HTTPC_ERROR_CONNECTION_REFUSED;
  }
  std::ostringstream request;
  request << "POST " << path_ << " HTTP/1.1\r\nHost: " << host_ << ":" << port_
          << "\r\n";
  for (size_t i = 0; i < headers_.size(); i++) request << headers_[i] << "\r\n";
  request << "Content-Length: " << size << "\r\nConnection: close\r\n\r\n";
  request.write(reinterpret_cast<const char*>(payload), static_cast<std::streamsize>(size));
  const std::string bytes = request.str();
  if (send(fd, bytes.data(), bytes.size(), 0) != static_cast<ssize_t>(bytes.size())) {
    close(fd);
    return HTTPC_ERROR_SEND_PAYLOAD_FAILED;
  }
  std::string response;
  char chunk[1024];
  for (;;) {
    const ssize_t n = recv(fd, chunk, sizeof(chunk), 0);
    if (n > 0) {
      response.append(chunk, static_cast<size_t>(n));
      continue;
    }
    if (n < 0 && (errno == EAGAIN || errno == EWOULDBLOCK) && response.empty()) {
      close(fd);
      return HTTPC_ERROR_READ_TIMEOUT;
    }
    break;
  }
  close(fd);
  const size_t split = response.find("\r\n\r\n");
  if (response.compare(0, 9, "HTTP/1.1 ") != 0 || split == std::string::npos) {
    return HTTPC_ERROR_READ_TIMEOUT;
  }
  body_ = response.substr(split + 4);
  return atoi(response.c_str() + 9);
}

String HTTPClient::getString(void) { return String(body_); }

// ---------------------------------------------------------------------------
// Preferences: key=value lines in a file
// ---------------------------------------------------------------------------

namespace {
std::map<std::string, std::string> loadPrefs(const std::string& path) {
  std::map<std::string, std::string> values;
  std::ifstream in(path.c_str());
  std::string line;
  while (std::getline(in, line)) {
    const size_t eq = line.find('=');
    if (eq != std::string::npos) values[line.substr(0, eq)] = line.substr(eq + 1);
  }
  return values;
}
}  // namespace

bool Preferences::begin(const char* name, bool readOnly, const char* partition_label) {
  (void)readOnly;
  (void)partition_label;
  const char* path = getenv("CLICKER_SIM_NVS");
  char fallback[96];
  snprintf(fallback, sizeof(fallback), "build/nvs-%012llx-%s.txt",
           static_cast<unsigned long long>(simMac()), name);
  path_ = path ? path : fallback;
  return true;
}

void Preferences::end() {}

bool Preferences::isKey(const char* key) { return loadPrefs(path_).count(key) > 0; }

String Preferences::getString(const char* key, String defaultValue) {
  std::map<std::string, std::string> values = loadPrefs(path_);
  return values.count(key) ? String(values[key]) : defaultValue;
}

size_t Preferences::putString(const char* key, const char* value) {
  std::map<std::string, std::string> values = loadPrefs(path_);
  values[key] = value;
  std::ofstream out(path_.c_str());
  for (std::map<std::string, std::string>::iterator it = values.begin();
       it != values.end(); ++it) {
    out << it->first << "=" << it->second << "\n";
  }
  return strlen(value);
}

// ---------------------------------------------------------------------------
// Simulator main loop
// ---------------------------------------------------------------------------

namespace {

const char* colorName(int red, int green, int blue) {
  static const char* names[8] = {"Off",  "Red",     "Green", "Yellow",
                                 "Blue", "Magenta", "Cyan",  "White"};
  const int on = LED_COMMON_ANODE ? LOW : HIGH;
  const int bits = (red == on ? 1 : 0) | (green == on ? 2 : 0) | (blue == on ? 4 : 0);
  return names[bits];
}

struct Release {
  int pin;
  unsigned long at;
};

}  // namespace

int main() {
  for (int i = 0; i < 32; i++) gLevel[i] = HIGH;
  setvbuf(stdout, nullptr, _IOLBF, 0);
  setup();

  std::vector<Release> releases;
  std::string lastColor;
  std::string pending;  // stdin bytes not yet split into lines
  bool running = true;
  while (running) {
    pollfd input;
    input.fd = 0;
    input.events = POLLIN;
    if (poll(&input, 1, 0) > 0) {
      char chunk[256];
      const ssize_t n = read(0, chunk, sizeof(chunk));
      if (n <= 0) running = false;
      if (n > 0) pending.append(chunk, static_cast<size_t>(n));
    }
    size_t newline;
    while ((newline = pending.find('\n')) != std::string::npos) {
      const std::string line = pending.substr(0, newline);
      pending.erase(0, newline + 1);
      std::istringstream words(line);
      std::string verb, arg;
      words >> verb >> arg;
      const int pin = arg.empty() ? -1 : pinFor(arg[0]);
      ::printf("SIM < %s\n", line.c_str());
      if (verb == "quit") {
        running = false;
      } else if (verb == "wifi") {
        simSetWifi(arg == "on");
      } else if (pin >= 0 && verb == "press") {
        firePressEdge(pin);  // a normal press: down for 120 ms
        Release r = {pin, millis() + 120};
        releases.push_back(r);
      } else if (pin >= 0 && verb == "tap") {
        firePressEdge(pin);  // so short that loop() never sees the pin LOW
        gLevel[pin] = HIGH;
      } else if (pin >= 0 && verb == "hold") {
        firePressEdge(pin);
      } else if (pin >= 0 && verb == "release") {
        gLevel[pin] = HIGH;
      }
    }
    for (size_t i = 0; i < releases.size();) {
      if (millis() >= releases[i].at) {
        gLevel[releases[i].pin] = HIGH;
        releases.erase(releases.begin() + static_cast<long>(i));
      } else {
        i++;
      }
    }

    loop();

    const std::string color = colorName(gLevel[PIN_LED_RED], gLevel[PIN_LED_GREEN],
                                        gLevel[PIN_LED_BLUE]);
    if (color != lastColor) {
      lastColor = color;
      ::printf("LED %s\n", color.c_str());
    }
  }
  return 0;
}
