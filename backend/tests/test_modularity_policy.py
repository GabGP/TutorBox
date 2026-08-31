from pathlib import Path

BACKEND_ROOT_DIRECTORY = Path(__file__).resolve().parent.parent
SOURCE_CODE_DIRECTORY = BACKEND_ROOT_DIRECTORY / "src"
TEST_SUITE_DIRECTORY = BACKEND_ROOT_DIRECTORY / "tests"

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
