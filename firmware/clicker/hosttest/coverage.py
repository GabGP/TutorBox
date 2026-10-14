"""Line coverage of the clicker's pure code, merged across the unit test objects.

run_tests.sh calls this with COVERAGE=1. gcov reports a header once per object that
includes it; this script merges those reports, so a line counts as covered when any
test reached it. It prints each source under clicker/src/ and any lines never run.

    python3 coverage.py <directory with the .gcda files> <clicker/src directory>
"""

import json
import subprocess
import sys
from pathlib import Path


def gcov_reports(build_dir: Path) -> list[dict]:
    """One gcov JSON report per object file."""
    reports = []
    for data_file in sorted(build_dir.glob("*.gcda")):
        output = subprocess.run(
            ["gcov", "--json-format", "--stdout", data_file.name],
            cwd=build_dir,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        reports.extend(json.loads(line) for line in output.splitlines() if line)
    return reports


def merged_line_counts(reports: list[dict], source_root: Path) -> dict[str, dict]:
    """{source path: {line number: highest execution count}} for sources under root."""
    counts: dict[str, dict] = {}
    for report in reports:
        for source in report["files"]:
            path = Path(source["file"]).resolve()
            if source_root not in path.parents:
                continue
            lines = counts.setdefault(str(path.relative_to(source_root)), {})
            for line in source["lines"]:
                number = line["line_number"]
                lines[number] = max(lines.get(number, 0), line["count"])
    return counts


def main() -> int:
    build_dir, source_root = Path(sys.argv[1]), Path(sys.argv[2]).resolve()
    counts = merged_line_counts(gcov_reports(build_dir), source_root)
    total = covered = files = 0
    for path in sorted(counts):
        lines = counts[path]
        if not lines:
            continue  # declarations only: nothing to run
        missed = sorted(number for number, count in lines.items() if count == 0)
        files += 1
        total += len(lines)
        covered += len(lines) - len(missed)
        percent = 100.0 * (len(lines) - len(missed)) / len(lines)
        note = f"   not run: {missed}" if missed else ""
        print(f"{percent:6.1f}%  {path}{note}")
    print(f"\n{100.0 * covered / total:.1f}% of {total} lines in {files} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
