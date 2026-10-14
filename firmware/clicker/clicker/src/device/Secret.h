// The secret a clicker logs in with: 128 random bits written as 32 lowercase hex
// characters. The clicker makes it once, from the hardware random number generator
// (esp32/SecretStore.cpp), and keeps it in flash.
// No Arduino calls in here, so it is unit-tested on a PC (hosttest/).
#pragma once

#include <stddef.h>
#include <stdint.h>

#include "../protocol/Protocol.h"

typedef FixedText<protocol::kSecretSize> Secret;

// How many 32-bit random words make one secret (each word gives 8 hex digits).
const size_t kSecretRandomWords = (protocol::kSecretSize - 1) / 8;

// True for exactly 32 lowercase hex characters, the shape the clicker makes itself.
bool isSecret(const char *text);

// Writes the random words as hex, most significant digit first.
Secret secretFromRandomWords(const uint32_t words[kSecretRandomWords]);
