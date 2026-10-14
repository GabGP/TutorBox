// StatusLed (timing) and LightPlan (which pattern for which situation).
#include <string.h>

#include "check.h"
#include "src/app/LightPlan.h"
#include "src/app/Phase.h"
#include "src/light/StatusLed.h"

static StatusLed::Pattern pattern(StatusLed::Color color, uint16_t onMs, uint16_t offMs)
{
  const StatusLed::Pattern made = {color, onMs, offMs};
  return made;
}

static bool samePattern(const StatusLed::Pattern &a, const StatusLed::Pattern &b)
{
  return a.color == b.color && a.onMs == b.onMs && a.offMs == b.offMs;
}

static void test_status_led()
{
  printf("StatusLed\n");
  StatusLed led;
  CHECK(led.colorAt(0) == StatusLed::Off);

  led.setPattern(pattern(StatusLed::Blue, 150, 150), 1000);
  CHECK(led.colorAt(1000) == StatusLed::Blue);
  CHECK(led.colorAt(1149) == StatusLed::Blue);
  CHECK(led.colorAt(1150) == StatusLed::Off);
  CHECK(led.colorAt(1300) == StatusLed::Blue);
  led.setPattern(pattern(StatusLed::Blue, 150, 150), 1200); // same pattern: rhythm kept
  CHECK(led.colorAt(1200) == StatusLed::Off);

  led.setPattern(pattern(StatusLed::White, 1, 0), 2000); // steady
  CHECK(led.colorAt(9999) == StatusLed::White);
  led.setPattern(pattern(StatusLed::Green, 0, 100), 2000); // onMs 0 = dark
  CHECK(led.colorAt(2000) == StatusLed::Off);

  led.setPattern(pattern(StatusLed::Green, 60, 2940), 3000);
  led.flash(StatusLed::Green, 1500, 3000);
  CHECK(led.overlayActive(3000));
  CHECK(led.colorAt(3500) == StatusLed::Green); // overlay, not the blip's dark part
  CHECK(led.colorAt(4499) == StatusLed::Green);
  CHECK(!led.overlayActive(4500));
  CHECK(led.colorAt(4500) == StatusLed::Off); // back to the blip (dark here)

  led.blink(StatusLed::Red, 3, 10000);
  CHECK(led.colorAt(10000) == StatusLed::Red);
  CHECK(led.colorAt(10150) == StatusLed::Off);
  CHECK(led.colorAt(10300) == StatusLed::Red);
  CHECK(led.colorAt(10600) == StatusLed::Red);
  CHECK(led.colorAt(10750) == StatusLed::Off);
  CHECK(led.overlayActive(10899));
  CHECK(!led.overlayActive(10900));
}

static void test_light_plan()
{
  printf("LightPlan, phase names\n");
  using light_plan::backgroundFor;
  // Outside Ready, the phase alone decides: votes and questions do not show.
  CHECK(samePattern(backgroundFor(Phase::LookingForWifi, true, true),
                    pattern(StatusLed::Blue, 150, 150)));
  CHECK(samePattern(backgroundFor(Phase::Connecting, false, false),
                    pattern(StatusLed::Blue, 1, 0)));
  CHECK(samePattern(backgroundFor(Phase::ServerUnreachable, false, false),
                    pattern(StatusLed::Blue, 1000, 1000)));
  CHECK(samePattern(backgroundFor(Phase::Rejected, false, false),
                    pattern(StatusLed::Magenta, 150, 150)));
  CHECK(samePattern(backgroundFor(Phase::Unassigned, false, false),
                    pattern(StatusLed::Magenta, 1000, 1000)));
  // Ready: sending beats a waiting question, which beats the idle blip.
  CHECK(samePattern(backgroundFor(Phase::Ready, true, true),
                    pattern(StatusLed::Yellow, 1, 0)));
  CHECK(samePattern(backgroundFor(Phase::Ready, false, true),
                    pattern(StatusLed::White, 700, 300)));
  CHECK(samePattern(backgroundFor(Phase::Ready, false, false),
                    pattern(StatusLed::Green, 60, 2940)));

  // The board's small LED: steady with Wi-Fi, a 150 ms blink without.
  CHECK(light_plan::statusLedOn(true, 160));
  CHECK(light_plan::statusLedOn(false, 0) && !light_plan::statusLedOn(false, 160));
  CHECK(light_plan::statusLedOn(false, 300));

  CHECK(strcmp(phaseName(Phase::LookingForWifi), "looking-for-wifi") == 0);
  CHECK(strcmp(phaseName(Phase::Connecting), "connecting") == 0);
  CHECK(strcmp(phaseName(Phase::ServerUnreachable), "server-unreachable") == 0);
  CHECK(strcmp(phaseName(Phase::Rejected), "rejected") == 0);
  CHECK(strcmp(phaseName(Phase::Unassigned), "unassigned") == 0);
  CHECK(strcmp(phaseName(Phase::Ready), "ready") == 0);
  CHECK(strcmp(phaseName(static_cast<Phase>(99)), "?") == 0);
}

void test_light()
{
  test_status_led();
  test_light_plan();
}
