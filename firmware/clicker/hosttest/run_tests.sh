#!/usr/bin/env bash
# Builds and runs the clicker's unit tests on a PC (Linux, macOS or WSL; needs g++).
# Same strict flags as the ESP32 2.x core: C++11, no RTTI, warnings are errors.
# Every pure source is compiled, that is all of clicker/src/ except esp32/.
#   COVERAGE=1 bash run_tests.sh   also prints line coverage per source (gcov 9+)
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
if [ -z "${ARDUINOJSON_DIR:-}" ]; then
  ARDUINOJSON_DIR="$here/.deps/ArduinoJson"
  [ -d "$ARDUINOJSON_DIR" ] || git clone --quiet --depth 1 --branch v7.4.3 \
    https://github.com/bblanchon/ArduinoJson "$ARDUINOJSON_DIR"
fi
src="$here/../clicker"
out="$here/build/unit"
rm -rf "$out"
mkdir -p "$out"
coverage_flags=()
[ "${COVERAGE:-0}" = "1" ] && coverage_flags=(--coverage -O0)

pure_sources=$(find "$src/src" -name '*.cpp' -not -path '*/esp32/*' | sort)
# shellcheck disable=SC2086
(cd "$out" && g++ -std=gnu++11 -fno-rtti -Wall -Wextra -Werror -O1 "${coverage_flags[@]}" \
  -I"$src" -I"$ARDUINOJSON_DIR/src" \
  "$here"/unit/*.cpp $pure_sources -o "$out/test_logic")
(cd "$out" && ./test_logic)

if [ "${COVERAGE:-0}" = "1" ]; then
  echo
  python3 "$here/coverage.py" "$out" "$src/src"
fi
