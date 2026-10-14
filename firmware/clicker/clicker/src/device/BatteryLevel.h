// Turns the battery voltage into the 0..100 the teacher's class list shows.
// No Arduino calls in here, so it is unit-tested on a PC (hosttest/).
#pragma once

// Straight line between empty and full, clamped to 0..100. -1 when the voltage is
// unknown (mv < 0) or the settings make no sense (full not above empty).
int batteryPercent(int mv, int emptyMv, int fullMv);
