#!/usr/bin/env bash
# Utz'tutor — apply the 25W clock caps that nvpmodel should have applied at boot.
#
# Why: on the Orin Nano Super dev kit, nvpmodel.service fails at boot ("Reboot required for
# changing to this power mode" with no answer), so the CPU and GPU max clocks stay at the
# MAXN_SUPER values. The caps are read from the 25W block of /etc/nvpmodel.conf, so no clock
# numbers are copied into this file.
#
# Run as root by utztutor-power.service. DRY_RUN=1 prints what would be written instead.
set -euo pipefail

CONF=/etc/nvpmodel.conf
GPU_MAX=/sys/devices/platform/17000000.gpu/devfreq_dev/max_freq
DRY_RUN=${DRY_RUN:-0}

# Print "<sysfs path> <value>" for each CPU_A78_* and GPU MAX_FREQ line in the 25W block.
caps() {
    awk -v gpu="$GPU_MAX" '
        /^< POWER_MODEL / { inside = ($0 ~ /NAME=25W[ >]/); next }
        inside && $2 == "MAX_FREQ" && $1 ~ /^CPU_A78_[0-9]+$/ {
            cpu = $1; sub(/^CPU_A78_/, "", cpu)
            print "/sys/devices/system/cpu/cpu" cpu "/cpufreq/scaling_max_freq", $3
        }
        inside && $1 == "GPU" && $2 == "MAX_FREQ" { print gpu, $3 }
    ' "$CONF"
}

# nvgpu creates the GPU devfreq node a few seconds after the kernel starts.
for _ in $(seq 30); do
    [ -e "$GPU_MAX" ] && break
    sleep 1
done

pairs=$(caps)
[ -n "$pairs" ] || { echo "no 25W MAX_FREQ entries in $CONF" >&2; exit 1; }

while read -r path value; do
    if [ "$DRY_RUN" = 1 ]; then
        echo "would set $path = $value"
        continue
    fi
    echo "$value" > "$path"
    got=$(cat "$path")
    [ "$got" = "$value" ] || { echo "$path reads $got, expected $value" >&2; exit 1; }
    echo "set $path = $value"
done <<< "$pairs"
