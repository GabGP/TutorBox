// The USB setup link: how a clicker gets the secret the TutorBox issued to it.
//
// With the clicker on a USB cable, a person typing in the Serial Monitor (or a
// setup tool) sends one line:
//   id                   the clicker answers with its device id
//   secret <32 hex>      the clicker stores the secret in flash and logs in with it
// Feed it every byte that arrives on the serial port. The secret is never echoed.
// No Arduino calls in here, so it is unit-tested on a PC (hosttest/).
#pragma once

#include <stddef.h>
#include <stdint.h>

#include "Protocol.h"

class SerialSetup {
 public:
  enum class Command : uint8_t {
    None,       // the line is not finished yet, or it was empty
    Identify,   // "id"
    Secret,     // "secret <32 lowercase hex>": read it with secret()
    BadSecret,  // "secret" followed by anything else
    Unknown
  };

  SerialSetup();

  // Returns a command when `c` ends a line, otherwise None.
  Command feed(char c);

  // The secret of the last Secret command. Call forget() once it is stored.
  const char* secret() const { return secret_; }
  void forget();

 private:
  Command parse();

  static const size_t kLineSize = 48;
  char line_[kLineSize];
  size_t length_;
  bool overflow_;  // the line was longer than any command: drop it whole
  char secret_[protocol::kSecretSize];
};
