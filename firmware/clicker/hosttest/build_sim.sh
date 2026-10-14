#!/usr/bin/env bash
# Builds the PC simulator: the real clicker.ino + Board.cpp + logic, with the ESP32's
# pins, Wi-Fi and flash replaced by sim/ stand-ins and real HTTP to a TutorBox.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
if [ -z "${ARDUINOJSON_DIR:-}" ]; then
  ARDUINOJSON_DIR="$here/.deps/ArduinoJson"
  [ -d "$ARDUINOJSON_DIR" ] || git clone --quiet --depth 1 --branch v7.4.3 \
    https://github.com/bblanchon/ArduinoJson "$ARDUINOJSON_DIR"
fi
mkdir -p "$here/build"
src="$here/../clicker"
g++ -std=gnu++11 -fno-rtti -Wall -Wextra -Werror -O1 \
  -I"$here/sim" -I"$src" -I"$ARDUINOJSON_DIR/src" \
  "$here/sim/sim_core.cpp" "$here/sim/sim_sketch.cpp" "$src/Board.cpp" \
  "$src/Buttons.cpp" "$src/StatusLed.cpp" "$src/Protocol.cpp" "$src/SerialSetup.cpp" \
  "$src/ClickerApp.cpp" \
  -o "$here/build/clicker_sim"
echo "built $here/build/clicker_sim"
