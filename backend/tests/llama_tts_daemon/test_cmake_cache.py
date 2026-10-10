"""Verifies the stale CMake cache check that decides whether the build folder is discarded."""

import pytest

from tools.llama_tts_daemon.build_llama import cmake_cache, paths
from tools.llama_tts_daemon.build_llama.console import TAG_INFO

CACHE_FILE_NAME = "CMakeCache.txt"
NINJA_CACHE = "CMAKE_GENERATOR:INTERNAL=Ninja\n"
OTHER_GENERATOR_CACHE = "CMAKE_GENERATOR:INTERNAL=Unix Makefiles\n"
MISSING_PROGRAM_LINE = "CMAKE_MAKE_PROGRAM:FILEPATH=CMAKE_MAKE_PROGRAM-NOTFOUND\n"
NINJA_AND_MISSING_PROGRAM_CACHE = NINJA_CACHE + MISSING_PROGRAM_LINE


def _write_cache(content: str) -> None:
    """Writes CMakeCache.txt with the given content into the build folder."""
    paths.BUILD_DIR.mkdir(parents=True, exist_ok=True)
    (paths.BUILD_DIR / CACHE_FILE_NAME).write_text(content, encoding="utf-8")


@pytest.mark.parametrize("has_ninja", [True, False])
def test_discard_stale_cache_ignores_missing_build_folder(
    build_tree, capsys, has_ninja
):
    """Verifies nothing is printed or created when the build folder does not exist."""
    cmake_cache.discard_stale_cache(has_ninja)
    assert not paths.BUILD_DIR.exists()
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("has_ninja", [True, False])
def test_discard_stale_cache_keeps_empty_build_folder(build_tree, capsys, has_ninja):
    """Verifies an empty build folder without CMakeCache.txt is kept and prints nothing."""
    paths.BUILD_DIR.mkdir(parents=True)
    cmake_cache.discard_stale_cache(has_ninja)
    assert paths.BUILD_DIR.is_dir()
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize(
    ("cache_content", "has_ninja"),
    [
        pytest.param(NINJA_CACHE, True, id="ninja-cache-ninja-chosen"),
        pytest.param(OTHER_GENERATOR_CACHE, False, id="other-cache-other-chosen"),
        pytest.param(MISSING_PROGRAM_LINE, False, id="missing-program-no-ninja"),
    ],
)
def test_discard_stale_cache_keeps_cache_matching_chosen_generator(
    build_tree, capsys, cache_content, has_ninja
):
    """Verifies a cache that matches the chosen generator is kept and prints nothing."""
    _write_cache(cache_content)
    cmake_cache.discard_stale_cache(has_ninja)
    assert (paths.BUILD_DIR / CACHE_FILE_NAME).is_file()
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize(
    ("cache_content", "has_ninja", "expected_reason"),
    [
        pytest.param(
            NINJA_CACHE,
            False,
            "Generator changed from Ninja to Other",
            id="ninja-cache-other-chosen",
        ),
        pytest.param(
            OTHER_GENERATOR_CACHE,
            True,
            "Generator changed from Other to Ninja",
            id="other-cache-ninja-chosen",
        ),
        pytest.param(
            NINJA_AND_MISSING_PROGRAM_CACHE,
            True,
            "stale CMAKE_MAKE_PROGRAM-NOTFOUND with ninja now resolvable",
            id="stale-program-ninja-chosen",
        ),
        pytest.param(
            MISSING_PROGRAM_LINE,
            True,
            "Generator changed from Other to Ninja",
            id="stale-program-without-ninja-marker",
        ),
        pytest.param(
            NINJA_AND_MISSING_PROGRAM_CACHE,
            False,
            "Generator changed from Ninja to Other",
            id="stale-program-other-chosen",
        ),
    ],
)
def test_discard_stale_cache_removes_build_folder_and_names_reason(
    build_tree, capsys, cache_content, has_ninja, expected_reason
):
    """Verifies a mismatched or stale cache removes the build folder and names the reason."""
    _write_cache(cache_content)
    cmake_cache.discard_stale_cache(has_ninja)
    assert not paths.BUILD_DIR.exists()
    assert capsys.readouterr().out == (
        f"{TAG_INFO} {expected_reason}. Cleaning build cache...\n"
    )


def test_marker_constants_match_cmake_cache_literals():
    """Verifies the marker constants hold the exact CMakeCache.txt lines they search for."""
    assert cmake_cache.NINJA_GENERATOR_MARKER == "CMAKE_GENERATOR:INTERNAL=Ninja"
    assert (
        cmake_cache.MISSING_MAKE_PROGRAM_MARKER
        == "CMAKE_MAKE_PROGRAM:FILEPATH=CMAKE_MAKE_PROGRAM-NOTFOUND"
    )
