"""Verifies binary discovery and installation of the llama-tts daemon artifacts."""

from pathlib import Path
from unittest.mock import patch

import pytest

from tools.llama_tts_daemon.build_llama import install, paths
from tools.llama_tts_daemon.build_llama.console import TAG_FAIL, TAG_OK

CANDIDATE_FOLDERS = [
    pytest.param(("bin",), id="bin"),
    pytest.param(("bin", "Release"), id="bin-Release"),
    pytest.param(("tools", "tts"), id="tools-tts"),
    pytest.param(("tools", "tts", "Release"), id="tools-tts-Release"),
]


def _write_file(file_path: Path, content: bytes) -> Path:
    """Creates the parent folders of file_path and writes content into it."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(content)
    return file_path


@pytest.mark.parametrize("folder_parts", CANDIDATE_FOLDERS)
def test_find_built_binary_returns_binary_from_each_candidate_folder(
    build_tree, folder_parts
):
    """Verifies llama-tts.exe is found in each of the four CMake build folders."""
    binary = _write_file(
        paths.BUILD_DIR.joinpath(*folder_parts, "llama-tts.exe"), b"binary"
    )
    with patch("platform.system", return_value="Windows"):
        assert install.find_built_binary() == binary


def test_find_built_binary_prefers_earlier_candidate_folder(build_tree):
    """Verifies the earlier candidate folder wins when the binary is in two of them."""
    earlier = _write_file(paths.BUILD_DIR / "bin" / "llama-tts.exe", b"first")
    _write_file(paths.BUILD_DIR / "tools" / "tts" / "llama-tts.exe", b"second")
    with patch("platform.system", return_value="Windows"):
        assert install.find_built_binary() == earlier


def test_find_built_binary_returns_none_when_no_candidate_exists(build_tree):
    """Verifies find_built_binary returns None when no build folder holds the binary."""
    with patch("platform.system", return_value="Windows"):
        assert install.find_built_binary() is None


def test_install_artifacts_exits_with_code_one_when_binary_is_missing(
    build_tree, capsys
):
    """Verifies a missing binary prints FAIL, exits with code 1 and keeps the cache folder."""
    with (
        patch("platform.system", return_value="Windows"),
        pytest.raises(SystemExit) as exit_info,
    ):
        install.install_artifacts()
    assert exit_info.value.code == 1
    assert paths.CACHE_BIN_DIR.is_dir()
    assert capsys.readouterr().out == (
        f"{TAG_FAIL} Compiled binary not found in {paths.BUILD_DIR}\n"
    )


def test_install_artifacts_copies_windows_binary_without_chmod(build_tree, capsys):
    """Verifies a Windows install copies llama-tts.exe as llama-tts-daemon.exe with no chmod."""
    _write_file(paths.BUILD_DIR / "bin" / "llama-tts.exe", b"windows-daemon")
    daemon_dest = paths.CACHE_BIN_DIR / "llama-tts-daemon.exe"
    license_dest = paths.CACHE_BIN_DIR / "LICENSE-llama-cpp"
    # copy2 reaches os.chmod through copystat, so copystat is isolated to observe
    # only the chmod calls made by install.py itself.
    with (
        patch("platform.system", return_value="Windows"),
        patch("shutil.copystat"),
        patch("os.chmod") as chmod_mock,
    ):
        install.install_artifacts()
    assert daemon_dest.read_bytes() == b"windows-daemon"
    chmod_mock.assert_not_called()
    assert capsys.readouterr().out == (
        f"{TAG_OK} Installed daemon binary : {daemon_dest}\n"
        f"{TAG_OK} Installed MIT license   : {license_dest}\n"
    )


def test_install_artifacts_makes_linux_daemon_executable_when_needed(build_tree):
    """Verifies a non-executable Linux daemon is chmod'ed to 0o755 after copying."""
    _write_file(paths.BUILD_DIR / "bin" / "llama-tts", b"linux-daemon")
    daemon_dest = paths.CACHE_BIN_DIR / "llama-tts-daemon"
    with (
        patch("platform.system", return_value="Linux"),
        patch("shutil.copystat"),
        patch("os.access", return_value=False),
        patch("os.chmod") as chmod_mock,
    ):
        install.install_artifacts()
    assert daemon_dest.read_bytes() == b"linux-daemon"
    chmod_mock.assert_called_once_with(daemon_dest, 0o755)


def test_install_artifacts_leaves_already_executable_linux_daemon_alone(build_tree):
    """Verifies a Linux daemon that is already executable is not chmod'ed again."""
    _write_file(paths.BUILD_DIR / "bin" / "llama-tts", b"linux-daemon")
    with (
        patch("platform.system", return_value="Linux"),
        patch("shutil.copystat"),
        patch("os.access", return_value=True),
        patch("os.chmod") as chmod_mock,
    ):
        install.install_artifacts()
    chmod_mock.assert_not_called()


def test_install_artifacts_copies_runtime_libraries_and_skips_other_files(
    build_tree, capsys
):
    """Verifies .dll, .so* and .dylib files beside the binary are installed, others skipped."""
    bin_dir = paths.BUILD_DIR / "bin"
    _write_file(bin_dir / "llama-tts.exe", b"daemon")
    _write_file(bin_dir / "ggml.dll", b"ggml")
    _write_file(bin_dir / "libllama.so.1", b"llama")
    _write_file(bin_dir / "libggml.dylib", b"ggml-mac")
    _write_file(bin_dir / "notes.txt", b"notes")
    with patch("platform.system", return_value="Windows"):
        install.install_artifacts()
    assert (paths.CACHE_BIN_DIR / "ggml.dll").read_bytes() == b"ggml"
    assert (paths.CACHE_BIN_DIR / "libllama.so.1").read_bytes() == b"llama"
    assert (paths.CACHE_BIN_DIR / "libggml.dylib").read_bytes() == b"ggml-mac"
    assert not (paths.CACHE_BIN_DIR / "notes.txt").exists()
    daemon_dest = paths.CACHE_BIN_DIR / "llama-tts-daemon.exe"
    license_dest = paths.CACHE_BIN_DIR / "LICENSE-llama-cpp"
    expected_output = "".join(
        f"{TAG_OK} Installed library      : {paths.CACHE_BIN_DIR / name}\n"
        for name in ["ggml.dll", "libllama.so.1", "libggml.dylib"]
    ) + (
        f"{TAG_OK} Installed daemon binary : {daemon_dest}\n"
        f"{TAG_OK} Installed MIT license   : {license_dest}\n"
    )
    assert capsys.readouterr().out == expected_output


def test_install_artifacts_prefers_bundled_license_over_upstream(build_tree):
    """Verifies the bundled LICENSE-llama-cpp is copied even when upstream has a LICENSE."""
    _write_file(paths.BUILD_DIR / "bin" / "llama-tts.exe", b"daemon")
    _write_file(paths.LICENSE_SRC, b"bundled MIT")
    _write_file(paths.SOURCE_DIR / "LICENSE", b"upstream MIT")
    with patch("platform.system", return_value="Windows"):
        install.install_artifacts()
    license_copy = paths.CACHE_BIN_DIR / "LICENSE-llama-cpp"
    assert license_copy.read_bytes() == b"bundled MIT"


def test_install_artifacts_falls_back_to_upstream_license(build_tree):
    """Verifies the upstream LICENSE is copied when the bundled license file is absent."""
    _write_file(paths.BUILD_DIR / "bin" / "llama-tts.exe", b"daemon")
    _write_file(paths.SOURCE_DIR / "LICENSE", b"upstream MIT")
    with patch("platform.system", return_value="Windows"):
        install.install_artifacts()
    license_copy = paths.CACHE_BIN_DIR / "LICENSE-llama-cpp"
    assert license_copy.read_bytes() == b"upstream MIT"


def test_install_artifacts_skips_license_file_when_no_source_exists(build_tree, capsys):
    """Verifies no license is written when neither source exists, yet the MIT line prints."""
    _write_file(paths.BUILD_DIR / "bin" / "llama-tts.exe", b"daemon")
    with patch("platform.system", return_value="Windows"):
        install.install_artifacts()
    license_dest = paths.CACHE_BIN_DIR / "LICENSE-llama-cpp"
    assert not license_dest.exists()
    assert f"{TAG_OK} Installed MIT license   : {license_dest}" in (
        capsys.readouterr().out
    )
