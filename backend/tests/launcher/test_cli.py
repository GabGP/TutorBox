"""Unit tests for the Utz'tutor launcher command-line flags (tools/launcher/cli.py)."""

import argparse
import sys

import pytest

from tools.launcher import cli


def _parse_flags(monkeypatch, *flags: str) -> argparse.Namespace:
    """Parses the given flags as if they were typed after run.py."""
    monkeypatch.setattr(sys, "argv", ["run.py", *flags])
    return cli.parse_arguments()


def test_defaults_when_no_flags_are_given(monkeypatch):
    """Verifies the launcher binds 0.0.0.0:8000 with every switch off by default."""
    arguments = _parse_flags(monkeypatch)
    assert arguments.host == "0.0.0.0"
    assert arguments.port == 8000
    assert arguments.no_reload is False
    assert arguments.no_build is False
    assert arguments.no_sync is False
    assert arguments.build_llama is False
    assert arguments.force_build_llama is False
    assert arguments.check_only is False
    assert arguments.download_models is None


def test_host_and_port_are_parsed(monkeypatch):
    """Verifies --host is kept as text and --port is converted to an integer."""
    arguments = _parse_flags(monkeypatch, "--host", "127.0.0.1", "--port", "9001")
    assert arguments.host == "127.0.0.1"
    assert arguments.port == 9001
    assert isinstance(arguments.port, int)


@pytest.mark.parametrize(
    ("flag", "attribute_name"),
    [
        ("--no-reload", "no_reload"),
        ("--no-build", "no_build"),
        ("--no-sync", "no_sync"),
        ("--build-llama", "build_llama"),
        ("--force-build-llama", "force_build_llama"),
        ("--check-only", "check_only"),
    ],
)
def test_boolean_flag_sets_its_attribute(monkeypatch, flag, attribute_name):
    """Verifies each boolean switch sets its matching attribute to True."""
    arguments = _parse_flags(monkeypatch, flag)
    assert getattr(arguments, attribute_name) is True


def test_download_models_without_value_selects_minimal(monkeypatch):
    """Verifies --download-models with no value selects the minimal voice tier."""
    arguments = _parse_flags(monkeypatch, "--download-models")
    assert arguments.download_models == "minimal"


def test_download_models_with_value_keeps_that_tier(monkeypatch):
    """Verifies --download-models all selects the all voice tier."""
    arguments = _parse_flags(monkeypatch, "--download-models", "all")
    assert arguments.download_models == "all"


def test_download_models_rejects_unknown_tier(monkeypatch):
    """Verifies an unknown --download-models tier makes argparse exit with code 2."""
    monkeypatch.setattr(sys, "argv", ["run.py", "--download-models", "bogus"])
    with pytest.raises(SystemExit) as exit_info:
        cli.parse_arguments()
    assert exit_info.value.code == 2
