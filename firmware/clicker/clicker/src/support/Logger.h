// printf-style log lines for the serial monitor. The logic never prints itself: it
// hands each line to a sink that clicker.ino (or a test) chooses.
#pragma once

class Logger
{
public:
  typedef void (*Sink)(const char *line);

  Logger() : sink_(nullptr) {}

  void setSink(Sink sink) { sink_ = sink; }

  // Formats one line (at most 159 characters) and passes it to the sink, if any.
  void printf(const char *format, ...) __attribute__((format(printf, 2, 3)));

private:
  Sink sink_;
};
