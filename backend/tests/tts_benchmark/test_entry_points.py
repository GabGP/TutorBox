"""Verifies the three benchmark scripts start their command lines and the package exports its API."""

import os
import subprocess
import sys

import pytest

import tools.benchmark.tts as tts_benchmark
from tools.benchmark.tts import ab, harness_melo, metrics
from tools.benchmark.tts.melo import cli as melo_cli
from tools.benchmark.tts.profiling import cli as profiling_cli
from tools.benchmark.tts.profiling.engine_run import profile_engine
from tools.benchmark.tts.profiling.results import EngineStats, ProfileResult
from tools.benchmark.tts.profiling.single_run import profile_speech_synthesis
from tools.benchmark.tts.shared import paths
from tools.benchmark.tts.sweep import cli as sweep_cli

SCRIPT_HELP_MARKERS = {
    "metrics.py": [
        "Benchmark Utz'tutor offline speech synthesis",
        "--engine",
        "--voice",
    ],
    "ab.py": ["TTS engine A/B sweep (Spanish-first)", "--engines", "--all-texts"],
    "harness_melo.py": ["MeloTTS Spanish ONNX harness", "--profile", "--provider"],
}
NATIVE_RUNTIME_MODULE_NAME = "onnxruntime"


def direct_run_environment() -> dict[str, str]:
    """Returns the environment for starting a script directly from another folder.

    Without PYTHONPYCACHEPREFIX exported, the script falls back to its own absolute
    .cache/pycache instead of resolving pytest's relative one against tmp_path.
    """
    return {
        name: value
        for name, value in os.environ.items()
        if name != "PYTHONPYCACHEPREFIX"
    }


def test_metrics_script_exposes_the_profiling_cli_main():
    """Verifies metrics.py starts the single-run profiler command line."""
    assert metrics.main is profiling_cli.main


def test_ab_script_exposes_the_sweep_cli_main():
    """Verifies ab.py starts the sweep command line."""
    assert ab.main is sweep_cli.main


def test_harness_melo_script_exposes_the_melo_cli_main():
    """Verifies harness_melo.py starts the MeloTTS harness command line."""
    assert harness_melo.main is melo_cli.main


def test_package_exports_the_profiling_api():
    """Verifies tools.benchmark.tts re-exports the two profilers and their result records."""
    assert tts_benchmark.__all__ == [
        "EngineStats",
        "ProfileResult",
        "profile_engine",
        "profile_speech_synthesis",
    ]
    assert tts_benchmark.EngineStats is EngineStats
    assert tts_benchmark.ProfileResult is ProfileResult
    assert tts_benchmark.profile_engine is profile_engine
    assert tts_benchmark.profile_speech_synthesis is profile_speech_synthesis


@pytest.mark.parametrize("script_name", sorted(SCRIPT_HELP_MARKERS))
def test_script_help_runs_from_any_directory(tmp_path, script_name):
    """Verifies each script prints its help when started as a script outside the repo root."""
    script_path = paths.BENCHMARK_DIR / script_name
    completed = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        cwd=str(tmp_path),
        env=direct_run_environment(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout.startswith(f"usage: {script_name}")
    for expected_text in SCRIPT_HELP_MARKERS[script_name]:
        assert expected_text in completed.stdout
    assert completed.stderr == ""


@pytest.mark.parametrize("script_name", sorted(SCRIPT_HELP_MARKERS))
def test_script_help_does_not_load_onnxruntime(tmp_path, script_name):
    """Verifies printing the help never imports onnxruntime, which logs host warnings on stderr."""
    script_path = paths.BENCHMARK_DIR / script_name
    # -X importtime lists every module the interpreter imports, one per stderr line.
    completed = subprocess.run(
        [sys.executable, "-X", "importtime", str(script_path), "--help"],
        cwd=str(tmp_path),
        env=direct_run_environment(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    imported_module_names = [
        import_line.rsplit("|", maxsplit=1)[-1].strip()
        for import_line in completed.stderr.splitlines()
    ]
    assert "argparse" in imported_module_names
    assert NATIVE_RUNTIME_MODULE_NAME not in imported_module_names
