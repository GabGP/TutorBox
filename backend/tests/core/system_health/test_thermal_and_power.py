"""thermal and power readers: present, missing, invalid and garbage files."""

from core.system_health.power import read_power_rails
from core.system_health.thermal import read_temperatures
from tests.core.system_health.fake_host import FakeHost


def test_temperatures_come_in_zone_order_named_by_their_type(tmp_path):
    host = FakeHost(tmp_path)
    host.write_thermal_zone(10, "soc2-thermal", "60437")
    host.write_thermal_zone(2, "cpu-thermal", "61531")
    host.write_thermal_zone(1, "gpu-thermal", "62437")

    readings = read_temperatures(tmp_path)

    assert [(reading.zone, reading.celsius) for reading in readings] == [
        ("gpu-thermal", 62.4),
        ("cpu-thermal", 61.5),
        ("soc2-thermal", 60.4),
    ]
    assert {reading.status for reading in readings} == {"ok"}


def test_a_zone_with_no_type_is_named_after_its_folder(tmp_path):
    host = FakeHost(tmp_path)
    host.write_thermal_zone(4, None, "50000")
    host.write_thermal_zone(5, "   ", "50000")

    names = [reading.zone for reading in read_temperatures(tmp_path)]

    assert names == ["thermal_zone4", "thermal_zone5"]


def test_impossible_or_unreadable_zones_are_left_out(tmp_path):
    host = FakeHost(tmp_path)
    host.write_thermal_zone(0, "cv0-thermal", "-256000")
    host.write_thermal_zone(1, "cv1-thermal", "No data available")
    host.write_thermal_zone(2, "cv2-thermal", None)
    host.write_thermal_zone(3, "hot-thermal", "200000")
    host.write_thermal_zone(4, "cpu-thermal", "70000")

    readings = read_temperatures(tmp_path)

    assert [reading.zone for reading in readings] == ["cpu-thermal"]


def test_temperature_statuses_follow_the_warn_and_critical_limits(tmp_path):
    host = FakeHost(tmp_path)
    host.write_thermal_zone(0, "warm-thermal", "80000")
    host.write_thermal_zone(1, "hot-thermal", "95000")

    statuses = [reading.status for reading in read_temperatures(tmp_path)]

    assert statuses == ["warn", "critical"]


def test_no_thermal_zones_gives_no_temperatures(tmp_path):
    assert read_temperatures(tmp_path) == []


def test_power_rails_give_milliwatts_from_millivolts_and_milliamps(tmp_path):
    host = FakeHost(tmp_path)
    host.write_rail(1, "VDD_IN", "4984", "1200")
    host.write_rail(2, "VDD_SOC", "4976", "224")

    rails = read_power_rails(tmp_path)

    assert [(rail.rail, rail.milliwatts) for rail in rails] == [
        ("VDD_IN", 5981),
        ("VDD_SOC", 1115),
    ]


def test_only_labelled_vdd_rails_with_both_readings_are_reported(tmp_path):
    host = FakeHost(tmp_path)
    host.write_rail(1, "VDD_IN", "4984", "1200")
    host.write_rail(2, "VDD_CPU_GPU_CV", "4976", None)  # no current: skipped
    host.write_rail(3, "VDD_SOC", None, "224")  # no voltage: skipped
    host.write_rail(4, "sum of shunt voltages", "8960", "5")  # not a VDD rail
    host.write_rail(5, None, "4984", "100")  # no label: skipped
    host.write_rail(6, "VDD_GPU", "garbage", "100")  # not a number: skipped
    host.write("sys/bus/i2c/drivers/ina3221/1-0040/hwmon/hwmon3/inx_label", "VDD_X\n")

    assert [rail.rail for rail in read_power_rails(tmp_path)] == ["VDD_IN"]


def test_power_is_empty_when_the_monitor_is_missing(tmp_path):
    assert read_power_rails(tmp_path) == []
