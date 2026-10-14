// ButtonBank and ResetGesture: from bouncy buttons to clean presses and the reset rule.
#include "check.h"
#include "src/input/ButtonBank.h"
#include "src/input/ResetGesture.h"

static void test_buttons()
{
  printf("ButtonBank\n");
  ButtonBank bank(30);
  ButtonSample pad = {};

  // Held at power-on: ignored until released.
  pad.pressed[0] = true;
  CHECK(pad.isDown('A') && !pad.isDown('D'));
  CHECK(bank.update(pad, 0) == 0);
  CHECK(bank.update(pad, 500) == 0);
  pad.pressed[0] = false;
  CHECK(bank.update(pad, 510) == 0);
  CHECK(bank.update(pad, 545) == 0); // re-armed here, no press

  // Press seen by the interrupt: reported at once, exactly once.
  pad.pressed[1] = true;
  pad.edges[1]++;
  CHECK(bank.update(pad, 600) == 'B');
  pad.edges[1] += 3; // bounce while pressed
  CHECK(bank.update(pad, 602) == 0);
  CHECK(bank.update(pad, 900) == 0); // long hold: still one press
  pad.pressed[1] = false;
  pad.edges[1] += 2; // release bounce
  CHECK(bank.update(pad, 905) == 0);
  CHECK(bank.update(pad, 940) == 0); // steady release: re-armed
  pad.pressed[1] = true;
  pad.edges[1]++;
  CHECK(bank.update(pad, 1000) == 'B'); // the next real press
  pad.pressed[1] = false;
  CHECK(bank.update(pad, 1100) == 0);
  CHECK(bank.update(pad, 1140) == 0);

  // A tap the loop never saw (it was busy on the network): the edge counts.
  pad.edges[2]++;
  CHECK(bank.update(pad, 2000) == 'C');
  CHECK(bank.update(pad, 2040) == 0);

  // No interrupt (it missed): a press held for 30 ms still counts.
  pad.pressed[3] = true;
  CHECK(bank.update(pad, 3000) == 0);
  CHECK(bank.update(pad, 3029) == 0);
  CHECK(bank.update(pad, 3030) == 'D');
  pad.pressed[3] = false;
  CHECK(bank.update(pad, 3100) == 0);
  CHECK(bank.update(pad, 3140) == 0);

  // Two buttons in the same instant: A wins, B is dropped, not reported later.
  pad.pressed[0] = pad.pressed[1] = true;
  pad.edges[0]++;
  pad.edges[1]++;
  CHECK(bank.update(pad, 4000) == 'A');
  CHECK(bank.update(pad, 4100) == 0);
  pad.pressed[0] = pad.pressed[1] = false;
  CHECK(bank.update(pad, 4200) == 0);
  CHECK(bank.update(pad, 4240) == 0);

  // Works across the 49-day millis() wrap.
  ButtonBank wrap(30);
  ButtonSample pad2 = {};
  const uint32_t t0 = 0xFFFFFFF0u;
  CHECK(wrap.update(pad2, t0) == 0);
  CHECK(wrap.update(pad2, t0 + 40) == 0); // wraps to 0x18
  pad2.edges[0]++;
  CHECK(wrap.update(pad2, t0 + 50) == 'A');
}

typedef ResetGesture::Result Gesture;

static void test_reset_gesture()
{
  printf("ResetGesture\n");
  const uint32_t kHoldMs = 5000;

  // Held from power-on: running until the hold time, decided exactly then.
  ResetGesture held(kHoldMs);
  CHECK(held.update(true, true, 1000) == Gesture::Holding);
  CHECK(held.update(true, true, 5999) == Gesture::Holding);   // 4999 ms: not yet
  CHECK(held.update(true, true, 6000) == Gesture::Confirmed); // exactly 5000 ms
  CHECK(held.update(true, true, 6100) == Gesture::Idle);      // decided: once only
  CHECK(held.update(false, false, 7000) == Gesture::Idle);

  // A let go before the hold time is cancelled, and it does not start again.
  ResetGesture letGoA(kHoldMs);
  CHECK(letGoA.update(true, true, 0) == Gesture::Holding);
  CHECK(letGoA.update(true, true, 4999) == Gesture::Holding);
  CHECK(letGoA.update(false, true, 4999) == Gesture::Cancelled); // A let go
  CHECK(letGoA.update(true, true, 5000) == Gesture::Idle);
  CHECK(letGoA.update(true, true, 20000) == Gesture::Idle);

  // D let go before the hold time: cancelled too.
  ResetGesture letGoD(kHoldMs);
  CHECK(letGoD.update(true, true, 0) == Gesture::Holding);
  CHECK(letGoD.update(true, false, 2000) == Gesture::Cancelled);
  CHECK(letGoD.update(true, true, 2500) == Gesture::Idle);

  // One millisecond before the hold time is still a cancel.
  ResetGesture almost(kHoldMs);
  CHECK(almost.update(true, true, 0) == Gesture::Holding);
  CHECK(almost.update(true, false, 4999) == Gesture::Cancelled);

  // One button alone at power-on: nothing, and pressing the other later does not start it.
  ResetGesture alone(kHoldMs);
  CHECK(alone.update(true, false, 0) == Gesture::Idle);
  CHECK(alone.update(true, true, 100) == Gesture::Idle);
  CHECK(alone.update(true, true, 6000) == Gesture::Idle);

  // A and D pressed after start-up (a press during a lesson): never armed.
  ResetGesture later(kHoldMs);
  CHECK(later.update(false, false, 0) == Gesture::Idle);
  CHECK(later.update(true, true, 100) == Gesture::Idle);
  CHECK(later.update(true, true, 6000) == Gesture::Idle);

  // millis() wraps around after 49 days: the hold still counts across the wrap.
  ResetGesture wrap(kHoldMs);
  const uint32_t start = 0xFFFFFFF0u;
  CHECK(wrap.update(true, true, start) == Gesture::Holding);
  CHECK(wrap.update(true, true, start + 4999) == Gesture::Holding);
  CHECK(wrap.update(true, true, start + 5000) == Gesture::Confirmed); // wraps to 0x1378
}

void test_input()
{
  test_buttons();
  test_reset_gesture();
}
