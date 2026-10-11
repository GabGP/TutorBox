"""Streaming HTTP download with an atomic rename, shared by every voice engine."""

import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from tools.voice_models.console import TAG_FAIL, TAG_INFO, TAG_OK

USER_AGENT = "Utz'tutor-Appliance-Downloader/1.0"
REQUEST_TIMEOUT_SECONDS = 60.0
CHUNK_SIZE_BYTES = 128 * 1024
BYTES_PER_MEGABYTE = 1024 * 1024


def _write_progress(display_name: str, downloaded_bytes: int, total_bytes: int) -> None:
    """Rewrites the current console line with the download percentage."""
    percent = downloaded_bytes / total_bytes * 100
    mb_done = downloaded_bytes / BYTES_PER_MEGABYTE
    mb_total = total_bytes / BYTES_PER_MEGABYTE
    sys.stdout.write(
        f"\r{TAG_INFO} {display_name}: {percent:5.1f}% "
        f"({mb_done:6.1f} / {mb_total:6.1f} MB)"
    )
    sys.stdout.flush()


def download_file(
    url: str,
    destination: Path,
    label: str = "",
    force: bool = False,
) -> bool:
    """Downloads a file via streaming HTTP GET with atomic write to a .part file."""
    if destination.is_file() and destination.stat().st_size > 0 and not force:
        print(f"{TAG_OK} Already present: {destination.name}")
        return True

    destination.parent.mkdir(parents=True, exist_ok=True)
    part_file = destination.with_suffix(destination.suffix + ".part")
    display_name = label or destination.name
    print(f"{TAG_INFO} Downloading {display_name}...")

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(
            request, timeout=REQUEST_TIMEOUT_SECONDS
        ) as response:
            total_bytes = int(response.headers.get("Content-Length", 0))
            downloaded_bytes = 0

            with open(part_file, "wb") as output_stream:
                while True:
                    chunk = response.read(CHUNK_SIZE_BYTES)
                    if not chunk:
                        break
                    output_stream.write(chunk)
                    downloaded_bytes += len(chunk)
                    if total_bytes > 0:
                        _write_progress(display_name, downloaded_bytes, total_bytes)

        if total_bytes > 0:
            sys.stdout.write("\n")
        os.replace(part_file, destination)
        print(f"{TAG_OK} Successfully downloaded: {destination.name}")
        return True
    except (urllib.error.URLError, TimeoutError, OSError) as err:
        if part_file.is_file():
            part_file.unlink(missing_ok=True)
        print(f"\n{TAG_FAIL} Failed to download {display_name}: {err}")
        return False
