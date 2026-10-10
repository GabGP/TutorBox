"""Tar extraction that refuses members escaping the destination directory."""

import tarfile
from pathlib import Path


def safe_extract_tar(tar_path: Path, target_dir: Path) -> None:
    """Safely extracts a tar archive ensuring members do not escape destination directory."""
    with tarfile.open(tar_path, "r:*") as archive:
        for member in archive.getmembers():
            target_path = (target_dir / member.name).resolve()
            if not str(target_path).startswith(str(target_dir.resolve())):
                raise RuntimeError(f"Path traversal detected in archive: {member.name}")
        archive.extractall(path=target_dir)
