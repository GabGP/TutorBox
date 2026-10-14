#include "BatterySensor.h"

#include <Arduino.h>

#include "../../config.h"
#include "../device/BatteryLevel.h"

int readBatteryPercent()
{
#if PIN_BATTERY_SENSE >= 0
  const int mv =
      static_cast<int>(analogReadMilliVolts(PIN_BATTERY_SENSE) * BATTERY_DIVIDER);
  return batteryPercent(mv, BATTERY_EMPTY_MV, BATTERY_FULL_MV);
#else
  return -1;
#endif
}
