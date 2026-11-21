"""A fake /proc and /sys under a temporary folder, written the way the Jetson kernel writes them."""

from pathlib import Path

GPU_DEVICE = "17000000.gpu"
THERMAL_ZONE_DIRECTORY = "sys/devices/virtual/thermal"
INA3221_HWMON = "sys/bus/i2c/drivers/ina3221/1-0040/hwmon/hwmon3"


class FakeHost:
    """Writes the kernel files a reader looks at, under `root`. Anything not written is missing."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def write(self, relative_path: str, text: str) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def write_cpu_stat(
        self, overall: list[int], cores: dict[int, list[int]], extra_lines: str = ""
    ) -> None:
        """/proc/stat with the aggregate line, one line per core and the lines no reader uses."""
        lines = ["cpu  " + " ".join(map(str, overall))]
        lines += [
            f"cpu{index} " + " ".join(map(str, counters))
            for index, counters in cores.items()
        ]
        lines += ["intr 12345 0 0", "ctxt 678", "btime 1700000000"]
        self.write("proc/stat", "\n".join(lines) + "\n" + extra_lines)

    def write_frequency_khz(self, index: int, khz: str) -> None:
        self.write(
            f"sys/devices/system/cpu/cpu{index}/cpufreq/scaling_cur_freq", khz + "\n"
        )

    def write_meminfo(
        self,
        total_kib: int,
        available_kib: int,
        swap_total_kib: int = 0,
        swap_free_kib: int = 0,
    ) -> None:
        self.write(
            "proc/meminfo",
            f"MemTotal:       {total_kib} kB\n"
            "MemFree:        2633716 kB\n"
            f"MemAvailable:   {available_kib} kB\n"
            "Buffers:          65464 kB\n"
            f"SwapTotal:      {swap_total_kib} kB\n"
            f"SwapFree:       {swap_free_kib} kB\n",
        )

    def write_gpu(
        self, load_per_mille: str, cur_hz: str | None, max_hz: str | None
    ) -> None:
        self.write(
            f"sys/devices/platform/bus@0/{GPU_DEVICE}/load", load_per_mille + "\n"
        )
        if cur_hz is not None:
            self.write(f"sys/class/devfreq/{GPU_DEVICE}/cur_freq", cur_hz + "\n")
        if max_hz is not None:
            self.write(f"sys/class/devfreq/{GPU_DEVICE}/max_freq", max_hz + "\n")

    def write_thermal_zone(
        self, index: int, zone_type: str | None, millidegrees: str | None
    ) -> None:
        zone = f"{THERMAL_ZONE_DIRECTORY}/thermal_zone{index}"
        if zone_type is not None:
            self.write(f"{zone}/type", zone_type + "\n")
        if millidegrees is not None:
            self.write(f"{zone}/temp", millidegrees + "\n")

    def write_rail(
        self,
        channel: int,
        label: str | None,
        millivolts: str | None,
        milliamps: str | None,
    ) -> None:
        if label is not None:
            self.write(f"{INA3221_HWMON}/in{channel}_label", label + "\n")
        if millivolts is not None:
            self.write(f"{INA3221_HWMON}/in{channel}_input", millivolts + "\n")
        if milliamps is not None:
            self.write(f"{INA3221_HWMON}/curr{channel}_input", milliamps + "\n")

    def write_uptime(self, text: str) -> None:
        self.write("proc/uptime", text + "\n")

    def write_loadavg(self, text: str) -> None:
        self.write("proc/loadavg", text + "\n")


def write_board(host: FakeHost) -> None:
    """A board that reads everything, with the values this Jetson showed on 2026-11-21."""
    host.write_cpu_stat(
        overall=[5244254, 25216, 838828, 52477141, 369858, 147643, 102026, 0],
        cores={
            0: [949984, 4654, 172908, 8554361, 59658, 68483, 42522, 0],
            1: [878709, 659, 152272, 8745162, 61194, 15963, 10813, 0],
        },
    )
    host.write_frequency_khz(0, "1190400")
    host.write_frequency_khz(1, "1344000")
    host.write_meminfo(total_kib=7665092, available_kib=3466988, swap_total_kib=0)
    host.write_gpu(load_per_mille="998", cur_hz="306000000", max_hz="918000000")
    host.write_thermal_zone(0, "cpu-thermal", "61531")
    host.write_thermal_zone(1, "gpu-thermal", "62437")
    host.write_thermal_zone(2, "cv0-thermal", "-256000")
    host.write_rail(1, "VDD_IN", "4984", "1200")
    host.write_rail(2, "VDD_CPU_GPU_CV", "4976", "224")
    host.write_rail(7, "sum of shunt voltages", "8960", None)
    host.write_uptime("98992.60 524771.45")
    host.write_loadavg("3.32 4.45 3.74 3/859 558475")
