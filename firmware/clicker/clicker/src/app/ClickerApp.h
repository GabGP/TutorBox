// The clicker's brain: what to send to the Utz'tutor, and what the LED should show.
//
// It never touches pins, Wi-Fi or HTTP itself. clicker.ino feeds it what happened
// (Wi-Fi up? which button? what did the server answer?) and does what it asks.
// That split lets hosttest/ run this exact code on a PC against a real backend.
//
// The parts it coordinates:
//   Connection    Wi-Fi, the login, the token, whether the server answers (the Phase)
//   Voting        which round is open, the vote being sent
//   Schedule      when the next poll and heartbeat are due
//   ReplyHandler  what each server reply changes in the three above
#pragma once

#include <stdint.h>

#include "../light/StatusLed.h"
#include "../support/Logger.h"
#include "Connection.h"
#include "Phase.h"
#include "ReplyHandler.h"
#include "Request.h"
#include "Schedule.h"
#include "Voting.h"

class ClickerApp
{
public:
  ClickerApp();
  // `secret` is the clicker's own, from SecretStore::loadOrCreate().
  void begin(const char *deviceId, const char *firmware, const char *secret,
             Logger::Sink log, uint32_t nowMs);

  // ---- what happened ----
  void setWifi(bool connected, uint32_t nowMs);
  void setVitals(int rssi, int batteryPct);
  void onButton(char option, uint32_t nowMs);
  void onResponse(RequestKind kind, int status, const char *body, uint32_t nowMs);

  // ---- what to do ----
  // One request at a time: after it returns true, nothing more until onResponse().
  bool nextRequest(uint32_t nowMs, Request &out);
  StatusLed::Color ledColor(uint32_t nowMs);
  bool statusLedOn(uint32_t nowMs) const;

  Phase phase() const { return connection_.phase(); }
  const char *phaseName() const { return ::phaseName(phase()); }
  // A question is open, this clicker has not answered it, no vote pending.
  bool armed() const;

private:
  void onButtonWhileNotReady(char option, uint32_t nowMs);

  // Declared before the parts that keep a reference to them.
  Logger log_;
  StatusLed led_;
  Schedule schedule_;

  Connection connection_;
  Voting voting_;
  ReplyHandler replies_;
  bool inFlight_; // a request was handed out and its reply has not come back yet
  int rssi_;
  int batteryPct_;
};
