from pathlib import Path

BACKEND_ROOT_DIRECTORY = Path(__file__).resolve().parent.parent
SOURCE_CODE_DIRECTORY = BACKEND_ROOT_DIRECTORY / "src"
TEST_SUITE_DIRECTORY = BACKEND_ROOT_DIRECTORY / "tests"
REPOSITORY_ROOT_DIRECTORY = BACKEND_ROOT_DIRECTORY.parent
LAUNCHER_ENTRY_POINT = REPOSITORY_ROOT_DIRECTORY / "run.py"
LAUNCHER_PACKAGE_DIRECTORY = REPOSITORY_ROOT_DIRECTORY / "tools" / "launcher"
DOWNLOADER_PACKAGE_DIRECTORY = REPOSITORY_ROOT_DIRECTORY / "tools" / "voice_models"
DAEMON_BUILD_PACKAGE_DIRECTORY = (
    REPOSITORY_ROOT_DIRECTORY / "tools" / "llama_tts_daemon"
)
BENCHMARK_PACKAGE_DIRECTORY = REPOSITORY_ROOT_DIRECTORY / "tools" / "benchmark"

MAX_PRODUCTION_MODULE_LINES_OF_CODE = 150
MAX_TEST_FILE_LINES_OF_CODE = 300


def test_production_modules_within_loc_ceiling():
    """Enforces that all production source files in backend/src/ are <= MAX_PRODUCTION_MODULE_LINES_OF_CODE."""
    oversized_modules: list[str] = []
    for source_file_path in sorted(SOURCE_CODE_DIRECTORY.rglob("*.py")):
        total_line_count = len(
            source_file_path.read_text(encoding="utf-8").splitlines()
        )
        if total_line_count > MAX_PRODUCTION_MODULE_LINES_OF_CODE:
            oversized_modules.append(
                f"{source_file_path.relative_to(BACKEND_ROOT_DIRECTORY)}: "
                f"{total_line_count} lines (ceiling: {MAX_PRODUCTION_MODULE_LINES_OF_CODE})"
            )

    assert not oversized_modules, (
        f"Found {len(oversized_modules)} production module(s) exceeding "
        f"{MAX_PRODUCTION_MODULE_LINES_OF_CODE} LoC:\n" + "\n".join(oversized_modules)
    )


def test_test_files_within_loc_ceiling():
    """Enforces that all test files in backend/tests/ are <= MAX_TEST_FILE_LINES_OF_CODE."""
    oversized_test_files: list[str] = []
    for test_file_path in sorted(TEST_SUITE_DIRECTORY.rglob("*.py")):
        total_line_count = len(test_file_path.read_text(encoding="utf-8").splitlines())
        if total_line_count > MAX_TEST_FILE_LINES_OF_CODE:
            oversized_test_files.append(
                f"{test_file_path.relative_to(BACKEND_ROOT_DIRECTORY)}: "
                f"{total_line_count} lines (ceiling: {MAX_TEST_FILE_LINES_OF_CODE})"
            )

    assert not oversized_test_files, (
        f"Found {len(oversized_test_files)} test file(s) exceeding "
        f"{MAX_TEST_FILE_LINES_OF_CODE} LoC:\n" + "\n".join(oversized_test_files)
    )


def test_launcher_modules_within_loc_ceiling():
    """Enforces that run.py and every module in tools/launcher/ are <= MAX_PRODUCTION_MODULE_LINES_OF_CODE."""
    launcher_source_file_paths = [
        LAUNCHER_ENTRY_POINT,
        *sorted(LAUNCHER_PACKAGE_DIRECTORY.rglob("*.py")),
    ]
    assert launcher_source_file_paths, (
        f"Expected run.py and modules under {LAUNCHER_PACKAGE_DIRECTORY} to exist"
    )
    oversized_launcher_modules: list[str] = []
    for launcher_source_file_path in launcher_source_file_paths:
        total_line_count = len(
            launcher_source_file_path.read_text(encoding="utf-8").splitlines()
        )
        if total_line_count > MAX_PRODUCTION_MODULE_LINES_OF_CODE:
            oversized_launcher_modules.append(
                f"{launcher_source_file_path.relative_to(REPOSITORY_ROOT_DIRECTORY)}: "
                f"{total_line_count} lines (ceiling: {MAX_PRODUCTION_MODULE_LINES_OF_CODE})"
            )

    assert not oversized_launcher_modules, (
        f"Found {len(oversized_launcher_modules)} launcher module(s) exceeding "
        f"{MAX_PRODUCTION_MODULE_LINES_OF_CODE} LoC:\n"
        + "\n".join(oversized_launcher_modules)
    )


def test_downloader_modules_within_loc_ceiling():
    """Enforces that every module in tools/voice_models/ is <= MAX_PRODUCTION_MODULE_LINES_OF_CODE."""
    downloader_source_file_paths = sorted(DOWNLOADER_PACKAGE_DIRECTORY.rglob("*.py"))
    assert downloader_source_file_paths, (
        f"Expected modules under {DOWNLOADER_PACKAGE_DIRECTORY} to exist"
    )
    oversized_downloader_modules: list[str] = []
    for downloader_source_file_path in downloader_source_file_paths:
        total_line_count = len(
            downloader_source_file_path.read_text(encoding="utf-8").splitlines()
        )
        if total_line_count > MAX_PRODUCTION_MODULE_LINES_OF_CODE:
            oversized_downloader_modules.append(
                f"{downloader_source_file_path.relative_to(REPOSITORY_ROOT_DIRECTORY)}: "
                f"{total_line_count} lines (ceiling: {MAX_PRODUCTION_MODULE_LINES_OF_CODE})"
            )

    assert not oversized_downloader_modules, (
        f"Found {len(oversized_downloader_modules)} downloader module(s) exceeding "
        f"{MAX_PRODUCTION_MODULE_LINES_OF_CODE} LoC:\n"
        + "\n".join(oversized_downloader_modules)
    )


def test_daemon_build_modules_within_loc_ceiling():
    """Enforces that build.py and every module in tools/llama_tts_daemon/ are <= MAX_PRODUCTION_MODULE_LINES_OF_CODE."""
    daemon_build_source_file_paths = sorted(
        DAEMON_BUILD_PACKAGE_DIRECTORY.rglob("*.py")
    )
    assert daemon_build_source_file_paths, (
        f"Expected modules under {DAEMON_BUILD_PACKAGE_DIRECTORY} to exist"
    )
    oversized_daemon_build_modules: list[str] = []
    for daemon_build_source_file_path in daemon_build_source_file_paths:
        total_line_count = len(
            daemon_build_source_file_path.read_text(encoding="utf-8").splitlines()
        )
        if total_line_count > MAX_PRODUCTION_MODULE_LINES_OF_CODE:
            oversized_daemon_build_modules.append(
                f"{daemon_build_source_file_path.relative_to(REPOSITORY_ROOT_DIRECTORY)}: "
                f"{total_line_count} lines (ceiling: {MAX_PRODUCTION_MODULE_LINES_OF_CODE})"
            )

    assert not oversized_daemon_build_modules, (
        f"Found {len(oversized_daemon_build_modules)} daemon build module(s) exceeding "
        f"{MAX_PRODUCTION_MODULE_LINES_OF_CODE} LoC:\n"
        + "\n".join(oversized_daemon_build_modules)
    )


def test_benchmark_modules_within_loc_ceiling():
    """Enforces that every module in tools/benchmark/ is <= MAX_PRODUCTION_MODULE_LINES_OF_CODE."""
    benchmark_source_file_paths = sorted(BENCHMARK_PACKAGE_DIRECTORY.rglob("*.py"))
    assert benchmark_source_file_paths, (
        f"Expected modules under {BENCHMARK_PACKAGE_DIRECTORY} to exist"
    )
    oversized_benchmark_modules: list[str] = []
    for benchmark_source_file_path in benchmark_source_file_paths:
        total_line_count = len(
            benchmark_source_file_path.read_text(encoding="utf-8").splitlines()
        )
        if total_line_count > MAX_PRODUCTION_MODULE_LINES_OF_CODE:
            oversized_benchmark_modules.append(
                f"{benchmark_source_file_path.relative_to(REPOSITORY_ROOT_DIRECTORY)}: "
                f"{total_line_count} lines (ceiling: {MAX_PRODUCTION_MODULE_LINES_OF_CODE})"
            )

    assert not oversized_benchmark_modules, (
        f"Found {len(oversized_benchmark_modules)} benchmark module(s) exceeding "
        f"{MAX_PRODUCTION_MODULE_LINES_OF_CODE} LoC:\n"
        + "\n".join(oversized_benchmark_modules)
    )
