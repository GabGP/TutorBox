// Sends the app's requests to the Utz'tutor (UTZTUTOR_URL in config.h) over one kept-open
// TCP connection: faster votes, less battery.
#pragma once

#include <Arduino.h>
#include <HTTPClient.h>
#include <WiFi.h>

#include "../app/Request.h"

class HttpLink
{
public:
  void begin();

  // Returns the HTTP status, or a negative HTTPClient error when the server could not
  // be reached. `reply` gets the body ("" for a 204).
  int send(const Request &request, String &reply);

private:
  WiFiClient client_;
  HTTPClient http_;
};
