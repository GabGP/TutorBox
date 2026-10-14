// Reads the battery through the optional voltage divider (config.h, PIN_BATTERY_SENSE).
#pragma once

// 0..100, or -1 when the two sense resistors are not fitted.
int readBatteryPercent();
