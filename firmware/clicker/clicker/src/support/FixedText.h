// A string that lives in a fixed char array: no heap, and no write past its end.
// The clicker keeps every id, token and secret in one of these.
#pragma once

#include <stddef.h>
#include <string.h>

// `Capacity` counts the closing '\0': FixedText<33> holds up to 32 characters.
template <size_t Capacity>
class FixedText
{
public:
  FixedText() { wipe(); }

  const char *c_str() const { return chars_; }
  bool isEmpty() const { return chars_[0] == '\0'; }
  bool equals(const char *other) const
  {
    return other != nullptr && strcmp(chars_, other) == 0;
  }

  // Copies as much of `source` as fits. A null `source` empties the text.
  void assignTruncated(const char *source)
  {
    if (source == nullptr)
      source = "";
    strncpy(chars_, source, Capacity - 1);
    chars_[Capacity - 1] = '\0';
  }

  // Copies `source` only when all of it fits and it is not empty; otherwise leaves the
  // text as it was and returns false. Half a token or half an id is worse than none.
  bool assignWhole(const char *source)
  {
    if (source == nullptr || source[0] == '\0' || strlen(source) >= Capacity)
    {
      return false;
    }
    assignTruncated(source);
    return true;
  }

  // Overwrites every byte, so a token or a secret does not linger in RAM.
  void wipe() { memset(chars_, 0, Capacity); }

  // For code that writes straight into the array (snprintf and the like).
  char *buffer() { return chars_; }
  static size_t capacity() { return Capacity; }

private:
  char chars_[Capacity];
};
