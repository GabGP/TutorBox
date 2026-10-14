#!/usr/bin/env bash
# Builds and runs the clicker's unit tests on a PC (Linux, macOS or WSL; needs g++).
# Same strict flags as the ESP32 2.x core: C++11, no RTTI, warnings are errors.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
deps="$here/.deps"
if [ -z "${ARDUINOJSON_DIR:-}" ]; then
  ARDUINOJSON_DIR="$deps/ArduinoJson"
  if [ ! -d "$ARDUINOJSON_DIR" ]; then
    git clone --quiet --depth 1 --branch v7.4.3 \
      https://github.com/bblanchon/ArduinoJson "$ARDUINOJSON_DIR"
  fi
fi
mkdir -p "$here/build"
src="$here/../clicker"
g++ -std=gnu++11 -fno-rtti -Wall -Wextra -Werror -O1 \
  -I"$src" -I"$ARDUINOJSON_DIR/src" \
  "$here/test_logic.cpp" "$src/Buttons.cpp" "$src/StatusLed.cpp" \
  "$src/Protocol.cpp" "$src/ResetGesture.cpp" "$src/ClickerApp.cpp" \
  -o "$here/build/test_logic"
"$here/build/test_logic"
