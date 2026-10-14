#!/usr/bin/env bash
# Builds the PC simulator: the real clicker.ino and all of clicker/src/ (esp32/ too),
# with the ESP32's pins, Wi-Fi and flash replaced by sim/ stand-ins and real HTTP to a
# Utz'tutor.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
if [ -z "${ARDUINOJSON_DIR:-}" ]; then
  ARDUINOJSON_DIR="$here/.deps/ArduinoJson"
  [ -d "$ARDUINOJSON_DIR" ] || git clone --quiet --depth 1 --branch v7.4.3 \
    https://github.com/bblanchon/ArduinoJson "$ARDUINOJSON_DIR"
fi
mkdir -p "$here/build"
src="$here/../clicker"
firmware_sources=$(find "$src/src" -name '*.cpp' | sort)
# shellcheck disable=SC2086
g++ -std=gnu++11 -fno-rtti -Wall -Wextra -Werror -O1 \
  -I"$here/sim" -I"$src" -I"$ARDUINOJSON_DIR/src" \
  "$here"/sim/*.cpp $firmware_sources \
  -o "$here/build/clicker_sim"
echo "built $here/build/clicker_sim"
