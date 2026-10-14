#!/usr/bin/env bash
# Builds and runs the clicker's unit tests on a PC (Linux, macOS or WSL; needs g++).
# Same strict flags as the ESP32 2.x core: C++11, no RTTI, warnings are errors.
# Every pure source is compiled, that is all of clicker/src/ except esp32/.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
if [ -z "${ARDUINOJSON_DIR:-}" ]; then
  ARDUINOJSON_DIR="$here/.deps/ArduinoJson"
  [ -d "$ARDUINOJSON_DIR" ] || git clone --quiet --depth 1 --branch v7.4.3 \
    https://github.com/bblanchon/ArduinoJson "$ARDUINOJSON_DIR"
fi
src="$here/../clicker"
out="$here/build/unit"
mkdir -p "$out"

pure_sources=$(find "$src/src" -name '*.cpp' -not -path '*/esp32/*' | sort)
# shellcheck disable=SC2086
g++ -std=gnu++11 -fno-rtti -Wall -Wextra -Werror -O1 \
  -I"$src" -I"$ARDUINOJSON_DIR/src" \
  "$here"/unit/*.cpp $pure_sources -o "$out/test_logic"
"$out/test_logic"
