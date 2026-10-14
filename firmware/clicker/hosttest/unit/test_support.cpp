// FixedText, Deadline, Interval and Logger: the pieces every other part leans on.
#include <string.h>

#include "check.h"
#include "src/support/Deadline.h"
#include "src/support/FixedText.h"
#include "src/support/Logger.h"

static void test_fixed_text()
{
  printf("FixedText\n");
  FixedText<6> text; // up to 5 characters
  CHECK(text.isEmpty() && strcmp(text.c_str(), "") == 0);
  CHECK(FixedText<6>::capacity() == 6);

  text.assignTruncated("abc");
  CHECK(text.equals("abc") && !text.isEmpty());
  text.assignTruncated("abcdefgh"); // cut to what fits, always closed with '\0'
  CHECK(text.equals("abcde"));
  text.assignTruncated(nullptr);
  CHECK(text.isEmpty());
  CHECK(!text.equals(nullptr));

  // Whole or nothing: a refusal leaves the old text in place.
  CHECK(text.assignWhole("xyz") && text.equals("xyz"));
  CHECK(!text.assignWhole("abcdef") && text.equals("xyz")); // 6 do not fit
  CHECK(text.assignWhole("abcde") && text.equals("abcde")); // 5 do
  CHECK(!text.assignWhole("") && text.equals("abcde"));
  CHECK(!text.assignWhole(nullptr) && text.equals("abcde"));

  // wipe() clears every byte, not just the first.
  text.wipe();
  const char *bytes = text.c_str();
  bool allZero = true;
  for (size_t i = 0; i < FixedText<6>::capacity(); i++)
    allZero = allZero && bytes[i] == 0;
  CHECK(allZero);
}

static void test_deadline_and_interval()
{
  printf("Deadline, Interval\n");
  Deadline deadline;
  CHECK(deadline.isDue(0)); // a new deadline is due at once
  deadline.dueIn(1000, 500);
  CHECK(!deadline.isDue(1499) && deadline.isDue(1500) && deadline.isDue(9000));
  deadline.dueNow(2000);
  CHECK(deadline.isDue(2000) && !deadline.isDue(1999));

  // Across the 49-day millis() wrap: due 16 ms after 0xFFFFFFF8 is 8 after the wrap.
  deadline.dueIn(0xFFFFFFF8u, 16);
  CHECK(!deadline.isDue(0xFFFFFFFFu) && !deadline.isDue(7) && deadline.isDue(8));

  Interval every(100);
  CHECK(!every.elapsed(99));
  CHECK(every.elapsed(100)); // a period has passed, and it starts again from 100
  CHECK(!every.elapsed(199) && every.elapsed(200));
  every.restart(250); // ran early: the next one is a whole period later
  CHECK(!every.elapsed(349) && every.elapsed(350));

  Interval wrap(100);
  CHECK(wrap.elapsed(0xFFFFFFF0u));
  CHECK(!wrap.elapsed(0x50) && wrap.elapsed(0x54)); // 100 ms after, across the wrap
}

static void test_logger()
{
  printf("Logger\n");
  Logger silent;
  silent.printf("nobody hears this %d", 1); // no sink: nothing happens, nothing breaks

  gLog.clear();
  Logger log;
  log.setSink(captureLog);
  log.printf("Vote %c counted (%d)", 'B', 200);
  CHECK(gLog.size() == 1 && gLog[0] == "Vote B counted (200)");

  const std::string longLine(300, 'x');
  log.printf("%s", longLine.c_str());
  CHECK(gLog.size() == 2 && gLog[1].size() == 159); // cut, never overrun
}

void test_support()
{
  test_fixed_text();
  test_deadline_and_interval();
  test_logger();
}
