#include "Board.h"

#include <Preferences.h>
#include <esp_system.h>
#if __has_include(<esp_random.h>)
#include <esp_random.h>  // esp_random() moved here in ESP-IDF 5 (Arduino core 3.x)
#endif

#include "config.h"

namespace {

// Bumped by the button interrupt, read by loop(). Both arrays are plain globals so
// they live in RAM: an interrupt must not read flash (flash can be busy).
volatile uint32_t gEdges[ButtonBank::kCount] = {0, 0, 0, 0};
uint8_t gButtonPins[ButtonBank::kCount] = {PIN_BUTTON_A, PIN_BUTTON_B, PIN_BUTTON_C,
                                           PIN_BUTTON_D};

void ARDUINO_ISR_ATTR onButtonEdge(void* arg) {
  const uintptr_t index = reinterpret_cast<uintptr_t>(arg);
  // Count it only if the pin is still LOW: this drops electrical spikes shorter than
  // the few microseconds it takes to get here.
  if (digitalRead(gButtonPins[index]) == LOW) {
    gEdges[index] = gEdges[index] + 1;
  }
}

void onWifiEvent(WiFiEvent_t event, WiFiEventInfo_t info) {
  if (event == ARDUINO_EVENT_WIFI_STA_GOT_IP) {
    Serial.printf("[wifi] connected: IP %s, signal %d dBm\n",
                  WiFi.localIP().toString().c_str(), WiFi.RSSI());
    return;
  }
  if (event != ARDUINO_EVENT_WIFI_STA_DISCONNECTED) return;
  const uint8_t reason = info.wifi_sta_disconnected.reason;
  Serial.printf("[wifi] not connected, reason %u (%s)\n", reason,
                WiFi.disconnectReasonName(static_cast<wifi_err_reason_t>(reason)));
  if (reason == WIFI_REASON_NO_AP_FOUND) {
    Serial.println("[wifi] hint: is the router on? Is WIFI_SSID in secrets.h exact?");
  } else if (reason == WIFI_REASON_AUTH_FAIL ||
             reason == WIFI_REASON_4WAY_HANDSHAKE_TIMEOUT ||
             reason == WIFI_REASON_HANDSHAKE_TIMEOUT) {
    Serial.println("[wifi] hint: check WIFI_PASSWORD in secrets.h");
  }
}

}  // namespace

void Board::begin() {
  Serial.begin(115200);
  delay(300);  // lets the USB serial monitor reattach after a reset

  pinMode(PIN_LED_RED, OUTPUT);
  pinMode(PIN_LED_GREEN, OUTPUT);
  pinMode(PIN_LED_BLUE, OUTPUT);
  showColor(StatusLed::Off);
#if PIN_STATUS_LED >= 0
  pinMode(PIN_STATUS_LED, OUTPUT);
  showStatus(false);
#endif

  for (uint8_t i = 0; i < ButtonBank::kCount; i++) {
    pinMode(gButtonPins[i], INPUT_PULLUP);
    attachInterruptArg(gButtonPins[i], onButtonEdge,
                       reinterpret_cast<void*>(static_cast<uintptr_t>(i)), FALLING);
  }

  // Identity: the last 3 bytes of the Wi-Fi MAC address, the same ones the router's
  // client list shows, so ESP32-A4CF12 there and on the case match.
  const uint64_t mac = ESP.getEfuseMac();
  const uint8_t b3 = static_cast<uint8_t>(mac >> 24);
  const uint8_t b4 = static_cast<uint8_t>(mac >> 32);
  const uint8_t b5 = static_cast<uint8_t>(mac >> 40);
  snprintf(deviceId_, sizeof(deviceId_), "ESP32-%02X%02X%02X", b3, b4, b5);
  snprintf(hostname_, sizeof(hostname_), "clicker-%02x%02x%02x", b3, b4, b5);

  Serial.println();
  Serial.println("=========== TutorBox clicker ===========");
  Serial.printf("Device id : %s   <- write it on the case\n", deviceId_);
  Serial.printf("Firmware  : %s\n", FIRMWARE_VERSION);
  Serial.printf("Wi-Fi     : %s\n", WIFI_SSID);
  Serial.printf("TutorBox  : %s\n", TUTORBOX_URL);
  Serial.println("=========================================");

  startWifi();
  loadOrCreateSecret();  // after the radio starts: it makes esp_random() truly random
  http_.setReuse(true);  // keep one TCP connection open: faster votes, less battery
}

void Board::startWifi() {
  WiFi.persistent(false);       // do not rewrite the password to flash on every boot
  WiFi.setHostname(hostname_);  // before mode(): the router lists "clicker-a4cf12"
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.setSleep(WIFI_POWER_SAVE != 0);
  WiFi.onEvent(onWifiEvent);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
#if WIFI_LOW_TX_POWER
  txPowerSet_ = WiFi.setTxPower(WIFI_POWER_8_5dBm);
#endif
  offlineSince_ = millis();
  lastJoinAttempt_ = offlineSince_;
}

void Board::loadOrCreateSecret() {
  Preferences prefs;
  prefs.begin("clicker", false);
  String saved = prefs.isKey("secret") ? prefs.getString("secret") : String();
  if (saved.length() == 32) {
    strncpy(secret_, saved.c_str(), sizeof(secret_) - 1);
    secret_[sizeof(secret_) - 1] = '\0';
  } else {
    // 128 random bits, kept in flash for good. The TutorBox stores only a hash.
    for (int i = 0; i < 4; i++) {
      snprintf(secret_ + i * 8, 9, "%08lx", static_cast<unsigned long>(esp_random()));
    }
    prefs.putString("secret", secret_);
    Serial.println("[clicker] first boot: created this clicker's secret");
  }
  prefs.end();
}

bool Board::wifiConnected() const { return WiFi.status() == WL_CONNECTED; }

void Board::maintainWifi(uint32_t nowMs) {
#if WIFI_LOW_TX_POWER
  if (!txPowerSet_) txPowerSet_ = WiFi.setTxPower(WIFI_POWER_8_5dBm);
#endif
  if (wifiConnected()) {
    offlineSince_ = nowMs;
    return;
  }
  if (nowMs - offlineSince_ > 180000UL) {
    Serial.println("[wifi] offline for 3 minutes: restarting the clicker");
    delay(100);
    ESP.restart();
  }
  if (nowMs - lastJoinAttempt_ > 20000UL) {
    lastJoinAttempt_ = nowMs;
    Serial.println("[wifi] still offline, joining again");
    WiFi.disconnect();
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  }
}

int Board::rssi() const { return WiFi.RSSI(); }

int Board::batteryMv() const {
#if PIN_BATTERY_SENSE >= 0
  return static_cast<int>(analogReadMilliVolts(PIN_BATTERY_SENSE) * BATTERY_DIVIDER);
#else
  return -1;
#endif
}

void Board::readButtons(bool pressed[ButtonBank::kCount],
                        uint32_t edges[ButtonBank::kCount]) const {
  for (uint8_t i = 0; i < ButtonBank::kCount; i++) {
    pressed[i] = digitalRead(gButtonPins[i]) == LOW;
    edges[i] = gEdges[i];
  }
}

int Board::post(const char* path, const char* body, char* reply, size_t replySize) {
  reply[0] = '\0';
  char url[128];
  snprintf(url, sizeof(url), "%s%s", TUTORBOX_URL, path);
  http_.setConnectTimeout(1500);
  http_.setTimeout(2500);
  if (!http_.begin(client_, url)) return HTTPC_ERROR_CONNECTION_REFUSED;
  http_.addHeader("Content-Type", "application/json");
  http_.addHeader("X-Clicker-Id", deviceId_);
  http_.addHeader("X-Clicker-Secret", secret_);
  const int status =
      http_.POST(reinterpret_cast<uint8_t*>(const_cast<char*>(body)), strlen(body));
  if (status > 0) {
    String text = http_.getString();
    strncpy(reply, text.c_str(), replySize - 1);
    reply[replySize - 1] = '\0';
  }
  http_.end();
  return status;
}

void Board::showColor(StatusLed::Color color) {
  if (static_cast<int>(color) == shownColor_) return;
  shownColor_ = color;
  const uint8_t on = LED_COMMON_ANODE ? LOW : HIGH;
  const uint8_t off = LED_COMMON_ANODE ? HIGH : LOW;
  digitalWrite(PIN_LED_RED, (color & StatusLed::Red) ? on : off);
  digitalWrite(PIN_LED_GREEN, (color & StatusLed::Green) ? on : off);
  digitalWrite(PIN_LED_BLUE, (color & StatusLed::Blue) ? on : off);
}

void Board::showStatus(bool on) {
#if PIN_STATUS_LED >= 0
  if (static_cast<int>(on) == shownStatus_) return;
  shownStatus_ = on;
  // Active-low LED: LOW lights it.
  digitalWrite(PIN_STATUS_LED, (on != (STATUS_LED_ACTIVE_LOW != 0)) ? HIGH : LOW);
#else
  (void)on;
#endif
}
