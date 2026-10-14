// Replies as the Utz'tutor sends them, and short-hands for driving a ClickerApp
// through them. Shared by the test_app_*.cpp files and test_protocol.cpp.
#pragma once

#include <stdint.h>

#include <string>

#include "src/app/ClickerApp.h"

typedef RequestKind Kind;

extern const char *const kSecret;
extern const char *const kToken;
extern const char *const kLoggedIn;     // 200 from the login: kToken for "ana"
extern const char *const kUnassigned;   // 403 from the login
extern const char *const kRefused;      // 401 from the login
extern const char *const kLockedOut;    // 429 from the login
extern const char *const kNoSession;    // 404 from the poll: no match is running
extern const char *const kSessionEnded; // 401 from the vote or the heartbeat

// GET /session/current as the backend sends it, question text included.
// roundId == nullptr: a match with no round yet.
std::string session(const char *sessionId, const char *roundId, const char *status);

// Takes the next request, which must be of `kind`, and answers it.
bool answer(ClickerApp &app, uint32_t nowMs, Kind kind, int status, const char *body);

// Answers the poll that is due at `nowMs`, and the heartbeat first if one is due too.
bool poll(ClickerApp &app, uint32_t nowMs, int status, const std::string &body);

// Powers on with kSecret, joins Wi-Fi and logs in; no match is running. Its log lines
// go to gLog.
void login(ClickerApp &app, uint32_t nowMs);
// The same first step, without the login: powered on, Wi-Fi up, login due.
void powerOn(ClickerApp &app, uint32_t nowMs);
