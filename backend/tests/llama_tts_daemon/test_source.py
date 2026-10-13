"""Verifies the upstream clone and the patch steps of the llama-tts build."""

import subprocess
from pathlib import Path
from unittest.mock import call, patch

import pytest

from tools.llama_tts_daemon.build_llama import paths, source
from tools.llama_tts_daemon.build_llama.console import TAG_FAIL, TAG_INFO, TAG_OK

RUN_CMD_TARGET = "tools.llama_tts_daemon.build_llama.source.run_cmd"
SUBPROCESS_RUN_TARGET = "subprocess.run"
CLONING_LINE = (
    f"{TAG_INFO} Cloning {source.UPSTREAM_REPO} (tag: {source.PINNED_TAG})...\n"
)


def _write_file(file_path: Path, content: bytes) -> Path:
    """Creates the parent folders of file_path and writes content into it."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(content)
    return file_path


def _write_patch_files() -> tuple[Path, Path]:
    """Creates both patch files in paths.PATCH_FILES and returns them in order."""
    daemon_patch, embedding_patch = paths.PATCH_FILES
    _write_file(daemon_patch, b"daemon patch")
    _write_file(embedding_patch, b"embedding patch")
    return daemon_patch, embedding_patch


def _fake_git_result(return_code: int) -> subprocess.CompletedProcess:
    """Builds the fake result that subprocess.run returns for the reverse check."""
    return subprocess.CompletedProcess(args=[], returncode=return_code)


def _clone_command(target_dir: Path) -> list[str]:
    """Returns the shallow git clone command that fetches release b11002."""
    return [
        "git",
        "clone",
        "--depth",
        "1",
        "--branch",
        "b11002",
        "https://github.com/ggerganov/llama.cpp.git",
        str(target_dir),
    ]


def _reverse_check_command(patch_file: Path) -> list[str]:
    """Returns the git command that checks whether the given patch is applied."""
    return [
        "git",
        "-C",
        str(paths.SOURCE_DIR),
        "apply",
        "--whitespace=nowarn",
        "--reverse",
        "--check",
        str(patch_file),
    ]


def _apply_command(patch_file: Path) -> list[str]:
    """Returns the git command that applies the given patch to the source tree."""
    return [
        "git",
        "-C",
        str(paths.SOURCE_DIR),
        "apply",
        "--whitespace=nowarn",
        str(patch_file),
    ]


def test_pinned_tag_and_upstream_repo_match_release_b11002():
    """Verifies the pinned tag is b11002 and the upstream is the ggerganov/llama.cpp repo."""
    assert source.PINNED_TAG == "b11002"
    assert source.UPSTREAM_REPO == "https://github.com/ggerganov/llama.cpp.git"


def test_clone_upstream_creates_parent_and_clones_when_source_is_absent(
    build_tree, capsys
):
    """Verifies a missing source directory gets its parent created and a shallow clone."""
    nested_source_dir = build_tree / "cache" / "build" / "llama.cpp"
    with (
        patch.object(paths, "SOURCE_DIR", nested_source_dir),
        patch(RUN_CMD_TARGET) as run_cmd_mock,
    ):
        source.clone_upstream()
    assert nested_source_dir.parent.is_dir()
    run_cmd_mock.assert_called_once_with(_clone_command(nested_source_dir))
    assert capsys.readouterr().out == CLONING_LINE


def test_clone_upstream_skips_clone_when_git_directory_exists(build_tree, capsys):
    """Verifies an existing clone with a .git folder is reused without running git."""
    (paths.SOURCE_DIR / ".git").mkdir(parents=True)
    with patch(RUN_CMD_TARGET) as run_cmd_mock:
        source.clone_upstream()
    run_cmd_mock.assert_not_called()
    assert capsys.readouterr().out == (
        f"{TAG_OK} Upstream repository already present at {paths.SOURCE_DIR}\n"
    )


def test_clone_upstream_force_removes_existing_tree_before_cloning(build_tree, capsys):
    """Verifies force=True deletes the existing clone tree and then clones again."""
    (paths.SOURCE_DIR / ".git").mkdir(parents=True)
    _write_file(paths.SOURCE_DIR / "README.md", b"stale checkout")
    with patch(RUN_CMD_TARGET) as run_cmd_mock:
        source.clone_upstream(force=True)
    assert not paths.SOURCE_DIR.exists()
    run_cmd_mock.assert_called_once_with(_clone_command(paths.SOURCE_DIR))
    assert capsys.readouterr().out == (
        f"{TAG_INFO} Removing existing build directory for clean rebuild: "
        f"{paths.SOURCE_DIR}\n"
        f"{CLONING_LINE}"
    )


def test_clone_upstream_force_without_source_only_clones(build_tree, capsys):
    """Verifies force=True on a missing source directory clones with no removal notice."""
    with patch(RUN_CMD_TARGET) as run_cmd_mock:
        source.clone_upstream(force=True)
    run_cmd_mock.assert_called_once_with(_clone_command(paths.SOURCE_DIR))
    assert capsys.readouterr().out == CLONING_LINE


def test_clone_upstream_keeps_directory_without_git_and_clones_into_it(
    build_tree, capsys
):
    """Verifies a source folder without .git is kept as it is and the clone still runs."""
    partial_file = _write_file(paths.SOURCE_DIR / "partial.txt", b"unfinished")
    with patch(RUN_CMD_TARGET) as run_cmd_mock:
        source.clone_upstream(force=False)
    assert partial_file.read_bytes() == b"unfinished"
    run_cmd_mock.assert_called_once_with(_clone_command(paths.SOURCE_DIR))
    assert capsys.readouterr().out == CLONING_LINE


def test_apply_patch_exits_with_code_one_when_patch_file_is_missing(build_tree, capsys):
    """Verifies a missing patch file prints FAIL, exits with code 1 and runs no git."""
    missing_patch = paths.PATCH_FILES[0]
    with (
        patch(
            SUBPROCESS_RUN_TARGET, return_value=_fake_git_result(0)
        ) as subprocess_mock,
        patch(RUN_CMD_TARGET) as run_cmd_mock,
        pytest.raises(SystemExit) as exit_info,
    ):
        source.apply_patch(missing_patch)
    assert exit_info.value.code == 1
    subprocess_mock.assert_not_called()
    run_cmd_mock.assert_not_called()
    assert capsys.readouterr().out == (
        f"{TAG_FAIL} Patch file not found at {missing_patch}\n"
    )


def test_apply_patch_skips_apply_when_reverse_check_succeeds(build_tree, capsys):
    """Verifies a clean reverse check means the patch is already applied and kept."""
    daemon_patch = _write_file(paths.PATCH_FILES[0], b"daemon patch")
    with (
        patch(
            SUBPROCESS_RUN_TARGET, return_value=_fake_git_result(0)
        ) as subprocess_mock,
        patch(RUN_CMD_TARGET) as run_cmd_mock,
    ):
        source.apply_patch(daemon_patch)
    subprocess_mock.assert_called_once_with(
        _reverse_check_command(daemon_patch), capture_output=True, check=False
    )
    run_cmd_mock.assert_not_called()
    assert capsys.readouterr().out == (
        f"{TAG_OK} Patch already applied: {daemon_patch.name}\n"
    )


def test_apply_patch_applies_when_reverse_check_fails(build_tree, capsys):
    """Verifies a failing reverse check triggers one forward apply and a success line."""
    daemon_patch = _write_file(paths.PATCH_FILES[0], b"daemon patch")
    with (
        patch(SUBPROCESS_RUN_TARGET, return_value=_fake_git_result(1)),
        patch(RUN_CMD_TARGET) as run_cmd_mock,
    ):
        source.apply_patch(daemon_patch)
    run_cmd_mock.assert_called_once_with(_apply_command(daemon_patch))
    assert capsys.readouterr().out == (
        f"{TAG_INFO} Applying patch: {daemon_patch.name}...\n"
        f"{TAG_OK} Applied patch: {daemon_patch.name}\n"
    )


def test_apply_patch_force_applies_even_when_reverse_check_succeeds(build_tree, capsys):
    """Verifies force=True re-applies the patch although the reverse check passed."""
    daemon_patch = _write_file(paths.PATCH_FILES[0], b"daemon patch")
    with (
        patch(SUBPROCESS_RUN_TARGET, return_value=_fake_git_result(0)),
        patch(RUN_CMD_TARGET) as run_cmd_mock,
    ):
        source.apply_patch(daemon_patch, force=True)
    run_cmd_mock.assert_called_once_with(_apply_command(daemon_patch))
    assert capsys.readouterr().out == (
        f"{TAG_INFO} Applying patch: {daemon_patch.name}...\n"
        f"{TAG_OK} Applied patch: {daemon_patch.name}\n"
    )


def test_apply_patches_applies_both_patches_in_order(build_tree, capsys):
    """Verifies apply_patches applies the daemon patch first and the embedding patch second."""
    daemon_patch, embedding_patch = _write_patch_files()
    with (
        patch(SUBPROCESS_RUN_TARGET, return_value=_fake_git_result(1)),
        patch(RUN_CMD_TARGET) as run_cmd_mock,
    ):
        source.apply_patches()
    assert run_cmd_mock.call_args_list == [
        call(_apply_command(daemon_patch)),
        call(_apply_command(embedding_patch)),
    ]
    assert capsys.readouterr().out == (
        f"{TAG_INFO} Applying patch: {daemon_patch.name}...\n"
        f"{TAG_OK} Applied patch: {daemon_patch.name}\n"
        f"{TAG_INFO} Applying patch: {embedding_patch.name}...\n"
        f"{TAG_OK} Applied patch: {embedding_patch.name}\n"
    )


def test_apply_patches_skips_applied_patch_and_still_applies_the_other(
    build_tree, capsys
):
    """Verifies an already applied daemon patch is skipped while the embedding patch is applied."""
    daemon_patch, embedding_patch = _write_patch_files()
    with (
        patch(
            SUBPROCESS_RUN_TARGET,
            side_effect=[_fake_git_result(0), _fake_git_result(1)],
        ),
        patch(RUN_CMD_TARGET) as run_cmd_mock,
    ):
        source.apply_patches()
    run_cmd_mock.assert_called_once_with(_apply_command(embedding_patch))
    assert capsys.readouterr().out == (
        f"{TAG_OK} Patch already applied: {daemon_patch.name}\n"
        f"{TAG_INFO} Applying patch: {embedding_patch.name}...\n"
        f"{TAG_OK} Applied patch: {embedding_patch.name}\n"
    )


def test_apply_patches_exits_with_code_one_when_second_patch_is_missing(
    build_tree, capsys
):
    """Verifies a missing embedding patch stops apply_patches with code 1 after the daemon patch."""
    daemon_patch, embedding_patch = paths.PATCH_FILES
    _write_file(daemon_patch, b"daemon patch")
    with (
        patch(SUBPROCESS_RUN_TARGET, return_value=_fake_git_result(1)),
        patch(RUN_CMD_TARGET) as run_cmd_mock,
        pytest.raises(SystemExit) as exit_info,
    ):
        source.apply_patches()
    assert exit_info.value.code == 1
    run_cmd_mock.assert_called_once_with(_apply_command(daemon_patch))
    assert capsys.readouterr().out == (
        f"{TAG_INFO} Applying patch: {daemon_patch.name}...\n"
        f"{TAG_OK} Applied patch: {daemon_patch.name}\n"
        f"{TAG_FAIL} Patch file not found at {embedding_patch}\n"
    )
