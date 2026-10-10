"""Verifies the Jetson UMA detection from the Tegra release file and the SoC family."""

from types import SimpleNamespace

import pytest

from tools.benchmark.tts.memory import jetson


@pytest.fixture
def marker_files(monkeypatch, tmp_path):
    """Points both Jetson marker paths at files inside tmp_path that start absent."""
    release_file = tmp_path / "nv_tegra_release"
    soc_family_file = tmp_path / "family"
    monkeypatch.setattr(jetson, "TEGRA_RELEASE_FILE", release_file)
    monkeypatch.setattr(jetson, "SOC_FAMILY_FILE", soc_family_file)
    return SimpleNamespace(release_file=release_file, soc_family_file=soc_family_file)


def use_platform(monkeypatch, platform_name: str, machine_name: str) -> None:
    """Replaces the sys and platform references seen by the jetson module."""
    monkeypatch.setattr(jetson, "sys", SimpleNamespace(platform=platform_name))
    monkeypatch.setattr(
        jetson, "platform", SimpleNamespace(machine=lambda: machine_name)
    )


def test_tegra_release_file_alone_marks_a_jetson(monkeypatch, marker_files):
    """Verifies the presence of the Tegra release file is enough on any platform."""
    marker_files.release_file.write_text("R35", encoding="utf-8")
    use_platform(monkeypatch, "linux", "x86_64")
    assert jetson.is_jetson_uma() is True


@pytest.mark.parametrize("soc_family_text", ["Tegra234", "TEGRA194", "tegra"])
def test_aarch64_linux_with_tegra_soc_family_is_a_jetson(
    monkeypatch, marker_files, soc_family_text
):
    """Verifies an aarch64 Linux SoC family naming Tegra in any case marks a Jetson."""
    marker_files.soc_family_file.write_text(soc_family_text, encoding="utf-8")
    use_platform(monkeypatch, "linux", "aarch64")
    assert jetson.is_jetson_uma() is True


def test_aarch64_linux_with_other_soc_family_is_not_a_jetson(monkeypatch, marker_files):
    """Verifies an aarch64 Linux SoC family without Tegra is not a Jetson."""
    marker_files.soc_family_file.write_text("Generic ARM", encoding="utf-8")
    use_platform(monkeypatch, "linux", "aarch64")
    assert jetson.is_jetson_uma() is False


def test_aarch64_linux_without_soc_family_file_is_not_a_jetson(
    monkeypatch, marker_files
):
    """Verifies an aarch64 Linux machine with no SoC family file is not a Jetson."""
    use_platform(monkeypatch, "linux", "aarch64")
    assert jetson.is_jetson_uma() is False


def test_x86_linux_with_tegra_soc_family_is_not_a_jetson(monkeypatch, marker_files):
    """Verifies the SoC family is ignored unless the machine is aarch64."""
    marker_files.soc_family_file.write_text("Tegra234", encoding="utf-8")
    use_platform(monkeypatch, "linux", "x86_64")
    assert jetson.is_jetson_uma() is False


def test_windows_is_not_a_jetson(monkeypatch, marker_files):
    """Verifies a Windows host without any marker file is not a Jetson."""
    use_platform(monkeypatch, "win32", "AMD64")
    assert jetson.is_jetson_uma() is False
