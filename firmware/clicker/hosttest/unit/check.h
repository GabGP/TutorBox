// The small test framework the unit tests share. CHECK(condition) counts the check
// and prints the file and line of a failure; main() (test_main.cpp) sums them up.
#pragma once

#include <stdio.h>

#include <string>
#include <vector>

extern int gChecks;
extern int gFailures;

#define CHECK(cond)                                            \
  do                                                           \
  {                                                            \
    gChecks++;                                                 \
    if (!(cond))                                               \
    {                                                          \
      gFailures++;                                             \
      printf("  FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond); \
    }                                                          \
  } while (0)

// Log lines the code under test printed, for checks on what a person would read.
extern std::vector<std::string> gLog;
void captureLog(const char *line);
bool logged(const char *fragment);
