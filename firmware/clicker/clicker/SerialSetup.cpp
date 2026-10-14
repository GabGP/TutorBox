#include "SerialSetup.h"

#include <string.h>

namespace {
const char kSecretPrefix[] = "secret ";
}  // namespace

SerialSetup::SerialSetup() : length_(0), overflow_(false) {
  line_[0] = '\0';
  secret_[0] = '\0';
}

SerialSetup::Command SerialSetup::feed(char c) {
  if (c != '\n' && c != '\r') {
    if (length_ < kLineSize - 1) {
      line_[length_++] = c;
    } else {
      overflow_ = true;
    }
    return Command::None;
  }
  line_[length_] = '\0';
  const Command command = overflow_ ? Command::Unknown : parse();
  memset(line_, 0, sizeof(line_));  // a secret does not stay in the line buffer
  length_ = 0;
  overflow_ = false;
  return command;
}

void SerialSetup::forget() { memset(secret_, 0, sizeof(secret_)); }

SerialSetup::Command SerialSetup::parse() {
  if (line_[0] == '\0') return Command::None;  // the "\n" of a "\r\n"
  if (strcmp(line_, "id") == 0) return Command::Identify;
  const size_t prefix = sizeof(kSecretPrefix) - 1;
  if (strncmp(line_, kSecretPrefix, prefix) != 0) {
    return strcmp(line_, "secret") == 0 ? Command::BadSecret : Command::Unknown;
  }
  if (!protocol::isSecret(line_ + prefix)) return Command::BadSecret;
  memcpy(secret_, line_ + prefix, protocol::kSecretSize);
  return Command::Secret;
}
