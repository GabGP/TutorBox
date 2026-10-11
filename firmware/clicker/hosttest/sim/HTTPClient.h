// PC stand-in for the Arduino-ESP32 HTTPClient (signatures as in 2.0.17 / 3.3.x).
// Speaks real HTTP/1.1 over a socket, so the firmware talks to a real TutorBox.
#pragma once

#include <string>
#include <vector>

#include "Arduino.h"
#include "WiFi.h"

#define HTTPC_ERROR_CONNECTION_REFUSED (-1)
#define HTTPC_ERROR_SEND_PAYLOAD_FAILED (-3)
#define HTTPC_ERROR_NOT_CONNECTED (-4)
#define HTTPC_ERROR_READ_TIMEOUT (-11)

class HTTPClient {
 public:
  bool begin(WiFiClient& client, String url);
  void end(void);
  void setReuse(bool reuse);
  void setConnectTimeout(int32_t connectTimeout);
  void setTimeout(uint16_t timeout);
  void addHeader(const String& name, const String& value, bool first = false,
                 bool replace = true);
  int POST(uint8_t* payload, size_t size);
  String getString(void);

 private:
  std::string host_;
  int port_ = 80;
  std::string path_;
  std::vector<std::string> headers_;
  std::string body_;
  uint16_t timeoutMs_ = 5000;
};
