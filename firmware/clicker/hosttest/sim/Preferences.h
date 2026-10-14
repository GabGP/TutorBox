// PC stand-in for the Arduino-ESP32 Preferences (NVS) library, saved to a file so the
// simulated clicker keeps its secret across restarts, like the real flash does.
#pragma once

#include "Arduino.h"

class Preferences {
 public:
  bool begin(const char* name, bool readOnly = false, const char* partition_label = NULL);
  void end();
  bool isKey(const char* key);
  String getString(const char* key, String defaultValue = String());
  size_t putString(const char* key, const char* value);
  bool remove(const char* key);

 private:
  std::string path_;
};
