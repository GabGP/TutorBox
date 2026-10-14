#include "Secret.h"

#include <string.h>

namespace
{
  const char kHexDigits[] = "0123456789abcdef";
  const size_t kSecretLength = protocol::kSecretSize - 1;
  const size_t kHexDigitsPerWord = 8;

  bool isLowercaseHex(char c) { return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'); }
} // namespace

bool isSecret(const char *text)
{
  if (text == nullptr || strlen(text) != kSecretLength)
    return false;
  for (size_t i = 0; i < kSecretLength; i++)
  {
    if (!isLowercaseHex(text[i]))
      return false;
  }
  return true;
}

Secret secretFromRandomWords(const uint32_t words[kSecretRandomWords])
{
  Secret secret;
  char *out = secret.buffer();
  for (size_t word = 0; word < kSecretRandomWords; word++)
  {
    for (size_t digit = 0; digit < kHexDigitsPerWord; digit++)
    {
      const unsigned shift = 28 - 4 * static_cast<unsigned>(digit);
      out[word * kHexDigitsPerWord + digit] = kHexDigits[(words[word] >> shift) & 0xF];
    }
  }
  return secret; // the constructor zeroed the rest, so it ends with '\0'
}
