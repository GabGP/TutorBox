#include "BatteryLevel.h"

int batteryPercent(int mv, int emptyMv, int fullMv)
{
  if (mv < 0 || fullMv <= emptyMv)
    return -1;
  if (mv <= emptyMv)
    return 0;
  if (mv >= fullMv)
    return 100;
  return static_cast<int>((static_cast<long>(mv - emptyMv) * 100) / (fullMv - emptyMv));
}
