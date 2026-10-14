#include "Logger.h"

#include <stdarg.h>
#include <stdio.h>

void Logger::printf(const char *format, ...)
{
  if (sink_ == nullptr)
    return;
  char line[160];
  va_list args;
  va_start(args, format);
  vsnprintf(line, sizeof(line), format, args);
  va_end(args);
  sink_(line);
}
