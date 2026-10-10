"""Verifies CUDA detection and the CMake configure and build steps of the llama-tts build."""

from types import SimpleNamespace
from unittest.mock import call, patch

import pytest

from tools.llama_tts_daemon.build_llama import compile as compile_step
from tools.llama_tts_daemon.build_llama import paths
from tools.llama_tts_daemon.build_llama.console import TAG_INFO, TAG_OK, TAG_WARN

COMPILE_MODULE = "tools.llama_tts_daemon.build_llama.compile"
CMAKE_BIN = "C:/Program Files/CMake/bin/cmake.exe"
NINJA_BIN = "C:/venv/Scripts/ninja.exe"
NVCC_BIN = "C:/CUDA/bin/nvcc.exe"
NINJA_CACHE_CONTENT = "CMAKE_GENERATOR:INTERNAL=Ninja\n"
CUDA_OK_LINE = f"{TAG_OK} CUDA toolkit detected. Compiling with GPU acceleration (-DGGML_CUDA=ON)...\n"
CUDA_WARN_LINE = (
    f"{TAG_WARN} CUDA compiler not detected in PATH. Falling back to CPU build...\n"
)


def _tool_table(cmake_path: str | None = CMAKE_BIN, ninja_path: str | None = NINJA_BIN):
    """Returns a resolve_tool side effect that answers from a fixed table."""
    return {"cmake": cmake_path, "ninja": ninja_path}.get


def _recorded_commands(run_mock) -> list[list[str]]:
    """Returns the command lists that the faked run_cmd received, in call order."""
    return [recorded.args[0] for recorded in run_mock.call_args_list]


@pytest.fixture
def build_host(build_tree, monkeypatch):
    """Fakes the host for build_binary: 8 CPUs, CMake and Ninja found, no CUDA, no commands run."""
    monkeypatch.delenv("CUDA_PATH", raising=False)
    monkeypatch.setattr(
        compile_step, "UNIX_CUDA_TOOLKIT_DIR", build_tree / "missing-cuda-toolkit"
    )
    with (
        patch("os.cpu_count", return_value=8) as cpu_count_mock,
        patch("shutil.which", return_value=None) as which_mock,
        patch(
            f"{COMPILE_MODULE}.resolve_tool", side_effect=_tool_table()
        ) as resolve_mock,
        patch(f"{COMPILE_MODULE}.run_cmd") as run_mock,
    ):
        yield SimpleNamespace(
            cpu_count=cpu_count_mock,
            which=which_mock,
            resolve_tool=resolve_mock,
            run_cmd=run_mock,
        )


def test_detect_cuda_skips_probing_when_cuda_is_disabled(build_host, capsys):
    """Verifies use_cuda=False returns False without probing for nvcc or printing anything."""
    build_host.which.return_value = NVCC_BIN
    assert compile_step.detect_cuda(use_cuda=False) is False
    build_host.which.assert_not_called()
    assert capsys.readouterr().out == ""


def test_detect_cuda_reports_nvcc_on_path(build_host, capsys):
    """Verifies an nvcc found on PATH counts as a CUDA toolkit and announces the GPU build."""
    build_host.which.return_value = NVCC_BIN
    assert compile_step.detect_cuda(use_cuda=True) is True
    build_host.which.assert_called_once_with("nvcc")
    assert capsys.readouterr().out == CUDA_OK_LINE


def test_detect_cuda_reports_cuda_path_variable(build_host, monkeypatch, capsys):
    """Verifies a CUDA_PATH variable alone counts as a CUDA toolkit."""
    monkeypatch.setenv("CUDA_PATH", "C:/CUDA/v12.4")
    assert compile_step.detect_cuda(use_cuda=True) is True
    assert capsys.readouterr().out == CUDA_OK_LINE


def test_detect_cuda_reports_existing_toolkit_directory(
    build_host, build_tree, monkeypatch, capsys
):
    """Verifies an existing toolkit directory alone counts as a CUDA toolkit."""
    toolkit_dir = build_tree / "usr-local-cuda"
    toolkit_dir.mkdir()
    monkeypatch.setattr(compile_step, "UNIX_CUDA_TOOLKIT_DIR", toolkit_dir)
    assert compile_step.detect_cuda(use_cuda=True) is True
    assert capsys.readouterr().out == CUDA_OK_LINE


def test_detect_cuda_warns_and_returns_false_without_any_toolkit(build_host, capsys):
    """Verifies that with no nvcc, CUDA_PATH or toolkit directory the CPU fallback is announced."""
    assert compile_step.detect_cuda(use_cuda=True) is False
    assert capsys.readouterr().out == CUDA_WARN_LINE


def test_build_binary_configures_then_builds_with_ninja_and_cuda(build_host, capsys):
    """Verifies the Ninja and CUDA configure and build commands run in order from the source folder."""
    build_host.which.return_value = NVCC_BIN
    compile_step.build_binary(use_cuda=True, force=False)
    expected_configure = [
        CMAKE_BIN,
        "-B",
        str(paths.BUILD_DIR),
        "-S",
        str(paths.SOURCE_DIR),
        "-DGGML_CUDA=ON",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DLLAMA_BUILD_TESTS=OFF",
        "-DLLAMA_BUILD_EXAMPLES=OFF",
        "-DLLAMA_BUILD_SERVER=OFF",
        "-G",
        "Ninja",
        f"-DCMAKE_MAKE_PROGRAM={NINJA_BIN}",
    ]
    expected_build = [
        CMAKE_BIN,
        "--build",
        str(paths.BUILD_DIR),
        "--target",
        "llama-tts",
        "--config",
        "Release",
        "--parallel",
        "8",
    ]
    assert build_host.run_cmd.call_args_list == [
        call(expected_configure, cwd=paths.SOURCE_DIR),
        call(expected_build, cwd=paths.SOURCE_DIR),
    ]
    assert paths.BUILD_DIR.is_dir()
    assert capsys.readouterr().out == (
        CUDA_OK_LINE
        + f"{TAG_INFO} Configuring CMake (jobs: 8, generator: Ninja)...\n"
        + f"{TAG_INFO} Compiling target 'llama-tts' across 8 threads...\n"
        + f"{TAG_OK} Compilation succeeded.\n"
    )


def test_build_binary_without_ninja_uses_default_generator(build_host, capsys):
    """Verifies a build without Ninja drops -G and CMAKE_MAKE_PROGRAM and reports generator: default."""
    build_host.resolve_tool.side_effect = _tool_table(ninja_path=None)
    compile_step.build_binary()
    configure = _recorded_commands(build_host.run_cmd)[0]
    assert "-G" not in configure
    assert not any(
        argument.startswith("-DCMAKE_MAKE_PROGRAM") for argument in configure
    )
    assert configure[-1] == "-DLLAMA_BUILD_SERVER=OFF"
    assert f"{TAG_INFO} Configuring CMake (jobs: 8, generator: default)...\n" in (
        capsys.readouterr().out
    )


def test_build_binary_cpu_only_disables_cuda_without_probing(build_host, capsys):
    """Verifies use_cuda=False configures -DGGML_CUDA=OFF and prints no CUDA line."""
    build_host.which.return_value = NVCC_BIN
    compile_step.build_binary(use_cuda=False)
    configure = _recorded_commands(build_host.run_cmd)[0]
    assert "-DGGML_CUDA=OFF" in configure
    assert "CUDA" not in capsys.readouterr().out


def test_build_binary_falls_back_to_cpu_when_cuda_is_requested_but_missing(
    build_host, capsys
):
    """Verifies a requested CUDA build without a toolkit warns and configures -DGGML_CUDA=OFF."""
    compile_step.build_binary(use_cuda=True)
    configure = _recorded_commands(build_host.run_cmd)[0]
    assert "-DGGML_CUDA=OFF" in configure
    assert capsys.readouterr().out.startswith(CUDA_WARN_LINE)


def test_build_binary_uses_literal_cmake_when_cmake_is_not_resolvable(build_host):
    """Verifies both CMake commands fall back to the bare name cmake when resolve_tool finds nothing."""
    build_host.resolve_tool.side_effect = _tool_table(cmake_path=None)
    compile_step.build_binary()
    commands = _recorded_commands(build_host.run_cmd)
    assert [command[0] for command in commands] == ["cmake", "cmake"]


def test_build_binary_uses_four_jobs_when_cpu_count_is_unknown(build_host, capsys):
    """Verifies an unknown CPU count falls back to four parallel jobs in both steps."""
    build_host.cpu_count.return_value = None
    compile_step.build_binary()
    build_command = _recorded_commands(build_host.run_cmd)[1]
    assert build_command[-2:] == ["--parallel", "4"]
    output = capsys.readouterr().out
    assert f"{TAG_INFO} Configuring CMake (jobs: 4, generator: Ninja)...\n" in output
    assert f"{TAG_INFO} Compiling target 'llama-tts' across 4 threads...\n" in output


def test_build_binary_force_cleans_existing_build_folder(build_host, capsys):
    """Verifies force=True announces and deletes the old build folder, then recreates it."""
    paths.BUILD_DIR.mkdir(parents=True)
    leftover_file = paths.BUILD_DIR / "leftover.txt"
    leftover_file.write_text("old", encoding="utf-8")
    compile_step.build_binary(force=True)
    assert not leftover_file.exists()
    assert paths.BUILD_DIR.is_dir()
    first_line = capsys.readouterr().out.splitlines()[0]
    assert first_line == f"{TAG_INFO} Cleaning CMake build directory: {paths.BUILD_DIR}"


def test_build_binary_force_without_build_folder_prints_no_cleaning_line(
    build_host, capsys
):
    """Verifies force=True on a fresh checkout creates the build folder without the cleaning line."""
    compile_step.build_binary(force=True)
    assert paths.BUILD_DIR.is_dir()
    assert "Cleaning CMake build directory" not in capsys.readouterr().out


def test_build_binary_discards_stale_ninja_cache_before_configuring(build_host, capsys):
    """Verifies a Ninja cache is discarded before configuring when Ninja is no longer resolvable."""
    build_host.resolve_tool.side_effect = _tool_table(ninja_path=None)
    paths.BUILD_DIR.mkdir(parents=True)
    cache_file = paths.BUILD_DIR / "CMakeCache.txt"
    cache_file.write_text(NINJA_CACHE_CONTENT, encoding="utf-8")
    compile_step.build_binary()
    assert not cache_file.exists()
    assert capsys.readouterr().out == (
        f"{TAG_INFO} Generator changed from Ninja to Other. Cleaning build cache...\n"
        + CUDA_WARN_LINE
        + f"{TAG_INFO} Configuring CMake (jobs: 8, generator: default)...\n"
        + f"{TAG_INFO} Compiling target 'llama-tts' across 8 threads...\n"
        + f"{TAG_OK} Compilation succeeded.\n"
    )
