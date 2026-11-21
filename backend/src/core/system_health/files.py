"""Reads the kernel's virtual files. Every helper answers None instead of raising."""

from collections.abc import Iterable
from pathlib import Path

__all__ = [
    "HOST_ROOT",
    "first_match",
    "in_numeric_order",
    "read_int",
    "read_text",
]

# The real machine's root. Readers take a root argument so tests can build a fake one.
HOST_ROOT = Path("/")


def read_text(path: Path) -> str | None:
    """The file's text, or None when it is missing, unreadable or a directory."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def read_int(path: Path) -> int | None:
    """The integer a file holds (sysfs writes one per file), or None when it does not hold one."""
    text = read_text(path)
    if text is None:
        return None
    try:
        return int(text.strip())
    except ValueError:
        return None


def in_numeric_order(paths: Iterable[Path]) -> list[Path]:
    """Sorts names such as thermal_zone2 before thermal_zone10, where plain sorting does not."""
    return sorted(paths, key=lambda path: (len(path.name), path.name))


def first_match(root: Path, pattern: str) -> Path | None:
    """The first path under root that matches the glob pattern, in numeric order."""
    matches = in_numeric_order(root.glob(pattern))
    return matches[0] if matches else None
