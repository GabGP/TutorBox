#!/usr/bin/env python3
"""Automated Model Downloader for TutorBox TTS Voices.

Downloads neural acoustic models for offline classroom speech synthesis:
- Piper / Sherpa Spanish Harvard baseline (VITS, ~76 MB)
- Kokoro-82M multilingual INT8 StyleTTS2 ONNX (~140 MB compressed)
- Qwen3-TTS 1.7B Base GGUF weights & mmproj (~1.5 GB)

Usage:
    python tools/download_models.py                   # Downloads minimal tier (Piper/Sherpa Spanish)
    python tools/download_models.py --target kokoro   # Downloads Kokoro-82M
    python tools/download_models.py --target qwen     # Downloads Qwen3-TTS GGUF
    python tools/download_models.py --target all      # Downloads all neural models
    python tools/download_models.py --check-only      # Checks model status without downloading
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tarfile
import urllib.error
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MODELS_DIR = ROOT_DIR / ".cache" / "models" / "tts"

TAG_OK = "[\033[32mOK\033[0m]"
TAG_INFO = "[\033[34mINFO\033[0m]"
TAG_WARN = "[\033[33mWARN\033[0m]"
TAG_FAIL = "[\033[31mFAIL\033[0m]"

PIPER_BASE_URL = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/sharvard/medium"
)
QWEN_BASE_URL = (
    "https://huggingface.co/ggml-org/Qwen3-TTS-12Hz-1.7B-Base-GGUF/resolve/main"
)
KOKORO_TAR_URL = (
    "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/"
    "kokoro-int8-multi-lang-v1_0.tar.bz2"
)


def _safe_extract_tar(tar_path: Path, target_dir: Path) -> None:
    """Safely extracts a tar archive ensuring members do not escape destination directory."""
    with tarfile.open(tar_path, "r:*") as archive:
        for member in archive.getmembers():
            target_path = (target_dir / member.name).resolve()
            if not str(target_path).startswith(str(target_dir.resolve())):
                raise RuntimeError(
                    f"Path traversal detected in archive: {member.name}"
                )
        archive.extractall(path=target_dir)


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

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "TutorBox-Appliance-Downloader/1.0"},
    )

    try:
        with urllib.request.urlopen(request, timeout=60.0) as response:
            total_bytes = int(response.headers.get("Content-Length", 0))
            downloaded_bytes = 0
            chunk_size = 128 * 1024

            with open(part_file, "wb") as output_stream:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    output_stream.write(chunk)
                    downloaded_bytes += len(chunk)
                    if total_bytes > 0:
                        percent = downloaded_bytes / total_bytes * 100
                        mb_done = downloaded_bytes / (1024 * 1024)
                        mb_total = total_bytes / (1024 * 1024)
                        sys.stdout.write(
                            f"\r{TAG_INFO} {display_name}: {percent:5.1f}% "
                            f"({mb_done:6.1f} / {mb_total:6.1f} MB)"
                        )
                        sys.stdout.flush()

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


def generate_sherpa_tokens(onnx_json_path: Path, output_tokens_path: Path) -> bool:
    """Generates tokens text file from Piper phoneme mapping for Sherpa compatibility."""
    if output_tokens_path.is_file() and output_tokens_path.stat().st_size > 0:
        return True
    if not onnx_json_path.is_file():
        return False
    try:
        with open(onnx_json_path, "r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)
        phoneme_map = data.get("phoneme_id_map", {})
        if not phoneme_map:
            return False
        with open(output_tokens_path, "w", encoding="utf-8") as file_handle:
            file_handle.writelines(
                f"{token} {ids[0]}\n" for token, ids in phoneme_map.items()
            )
        print(f"{TAG_OK} Generated Sherpa tokens: {output_tokens_path.name}")
        return True
    except (OSError, json.JSONDecodeError) as err:
        print(f"{TAG_WARN} Could not generate tokens: {err}")
        return False


def generate_sherpa_model(
    onnx_path: Path, onnx_json_path: Path, output_sherpa_path: Path, force: bool = False
) -> bool:
    """Injects VITS metadata into Piper ONNX model for Sherpa-ONNX compatibility."""
    if output_sherpa_path.is_file() and output_sherpa_path.stat().st_size > 0 and not force:
        return True
    if not onnx_path.is_file() or not onnx_json_path.is_file():
        return False
    try:
        import onnx

        with open(onnx_json_path, "r", encoding="utf-8") as file_handle:
            cfg = json.load(file_handle)

        sample_rate = str(cfg.get("audio", {}).get("sample_rate", 22050))
        voice = str(cfg.get("espeak", {}).get("voice", "es"))
        num_speakers = str(cfg.get("num_speakers", 1))

        model = onnx.load(str(onnx_path))
        existing_keys = {p.key for p in model.metadata_props}
        meta = {
            "sample_rate": sample_rate,
            "n_speakers": num_speakers,
            "model_type": "vits",
            "comment": "piper",
            "language": voice,
            "voice": voice,
            "has_espeak": "1",
        }
        for k, v in meta.items():
            if k not in existing_keys:
                p = model.metadata_props.add()
                p.key = k
                p.value = str(v)

        onnx.save(model, str(output_sherpa_path))
        print(f"{TAG_OK} Generated Sherpa model: {output_sherpa_path.name}")
        return True
    except Exception as err:  # noqa: BLE001
        print(f"{TAG_WARN} Could not generate Sherpa model metadata: {err}")
        return False


def download_piper(models_dir: Path, force: bool = False) -> bool:
    """Downloads Piper / Sherpa Spanish Harvard ONNX model and config."""
    onnx_file = models_dir / "es_ES-sharvard-medium.onnx"
    json_file = models_dir / "es_ES-sharvard-medium.onnx.json"
    tokens_file = models_dir / "tokens_es_ES-sharvard-medium.txt"
    sherpa_file = models_dir / "es_ES-sharvard-medium.sherpa.onnx"

    onnx_ok = download_file(
        f"{PIPER_BASE_URL}/es_ES-sharvard-medium.onnx",
        onnx_file,
        label="Spanish Harvard ONNX model (~76 MB)",
        force=force,
    )
    json_ok = download_file(
        f"{PIPER_BASE_URL}/es_ES-sharvard-medium.onnx.json",
        json_file,
        label="Spanish Harvard ONNX config (~5 KB)",
        force=force,
    )

    if json_ok and onnx_ok:
        generate_sherpa_tokens(json_file, tokens_file)
        generate_sherpa_model(onnx_file, json_file, sherpa_file, force=force)

    return onnx_ok and json_ok


def download_kokoro(models_dir: Path, force: bool = False) -> bool:
    """Downloads and extracts Kokoro-82M multilingual INT8 ONNX bundle."""
    kokoro_dir = models_dir / "kokoro-int8-multi-lang-v1_0"
    voices_file = kokoro_dir / "voices.bin"
    model_file = kokoro_dir / "model.onnx"
    int8_model_file = kokoro_dir / "model.int8.onnx"

    if (
        kokoro_dir.is_dir()
        and voices_file.is_file()
        and (model_file.is_file() or int8_model_file.is_file())
        and not force
    ):
        print(f"{TAG_OK} Already present: Kokoro-82M bundle ({kokoro_dir.name})")
        return True

    tar_path = models_dir / "kokoro-int8-multi-lang-v1_0.tar.bz2"
    archive_ok = download_file(
        KOKORO_TAR_URL,
        tar_path,
        label="Kokoro-82M INT8 archive (~140 MB)",
        force=force,
    )
    if not archive_ok:
        return False

    print(f"{TAG_INFO} Extracting Kokoro-82M archive...")
    try:
        _safe_extract_tar(tar_path, models_dir)
        tar_path.unlink(missing_ok=True)
        print(f"{TAG_OK} Extracted Kokoro-82M model to {kokoro_dir.name}")
        return True
    except (OSError, tarfile.TarError) as err:
        print(f"{TAG_FAIL} Extraction failed: {err}")
        return False


def download_qwen(models_dir: Path, force: bool = False) -> bool:
    """Downloads Qwen3-TTS 1.7B Base GGUF weights and multimodal projector."""
    qwen_dir = models_dir / "qwen"
    gguf_file = qwen_dir / "Qwen3-TTS-12Hz-1.7B-Base-Q4_K_M.gguf"
    mmproj_file = qwen_dir / "mmproj-Qwen3-TTS-12Hz-1.7B-Base-Q8_0.gguf"

    gguf_ok = download_file(
        f"{QWEN_BASE_URL}/Qwen3-TTS-12Hz-1.7B-Base-Q4_K_M.gguf",
        gguf_file,
        label="Qwen3-TTS Base Q4_K_M GGUF (~1.03 GB)",
        force=force,
    )
    mmproj_ok = download_file(
        f"{QWEN_BASE_URL}/mmproj-Qwen3-TTS-12Hz-1.7B-Base-Q8_0.gguf",
        mmproj_file,
        label="Qwen3-TTS mmproj Q8_0 GGUF (~446 MB)",
        force=force,
    )

    return gguf_ok and mmproj_ok


def check_models(models_dir: Path) -> dict[str, bool]:
    """Checks status of all three neural engine models."""
    piper_file = models_dir / "es_ES-sharvard-medium.onnx"
    kokoro_dir = models_dir / "kokoro-int8-multi-lang-v1_0"
    kokoro_voices = kokoro_dir / "voices.bin"
    qwen_dir = models_dir / "qwen"
    qwen_gguf = qwen_dir / "Qwen3-TTS-12Hz-1.7B-Base-Q4_K_M.gguf"
    qwen_mmproj = qwen_dir / "mmproj-Qwen3-TTS-12Hz-1.7B-Base-Q8_0.gguf"

    return {
        "piper": piper_file.is_file() and piper_file.stat().st_size > 0,
        "kokoro": kokoro_dir.is_dir()
        and kokoro_voices.is_file()
        and kokoro_voices.stat().st_size > 0,
        "qwen": qwen_gguf.is_file()
        and qwen_gguf.stat().st_size > 0
        and qwen_mmproj.is_file()
        and qwen_mmproj.stat().st_size > 0,
    }


def execute_download(
    target: str = "minimal",
    models_dir: Path | None = None,
    force: bool = False,
) -> bool:
    """Coordinates download based on requested target tier."""
    effective_dir = models_dir or DEFAULT_MODELS_DIR
    effective_dir.mkdir(parents=True, exist_ok=True)

    success = True
    if target in ("minimal", "piper", "all"):
        success = download_piper(effective_dir, force=force) and success
    if target in ("kokoro", "all"):
        success = download_kokoro(effective_dir, force=force) and success
    if target in ("qwen", "all"):
        success = download_qwen(effective_dir, force=force) and success

    return success


def main() -> None:
    """CLI entrypoint for TutorBox model downloader."""
    parser = argparse.ArgumentParser(
        description="Download offline voice models for TutorBox"
    )
    parser.add_argument(
        "--target",
        choices=["minimal", "piper", "kokoro", "qwen", "all"],
        default="minimal",
        help="Target voice engine models to download (default: minimal)",
    )
    parser.add_argument(
        "--models-dir",
        type=Path,
        default=DEFAULT_MODELS_DIR,
        help="Destination directory for models (default: .cache/models/tts)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download of existing models",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Check presence of models and exit without downloading",
    )
    args = parser.parse_args()

    status = check_models(args.models_dir)
    print("==================================================")
    print("         TutorBox TTS Models Diagnostic           ")
    print("==================================================")
    print(
        f"  * Piper / Sherpa (Spanish) : "
        f"{TAG_OK if status['piper'] else TAG_WARN + ' Missing'}"
    )
    print(
        f"  * Kokoro-82M (Multilingual): "
        f"{TAG_OK if status['kokoro'] else TAG_WARN + ' Missing'}"
    )
    print(
        f"  * Qwen3-TTS (GGUF Weights) : "
        f"{TAG_OK if status['qwen'] else TAG_WARN + ' Missing'}"
    )
    print("--------------------------------------------------")

    if args.check_only:
        missing_count = sum(1 for present in status.values() if not present)
        sys.exit(1 if missing_count > 0 else 0)

    print(f"Downloading target tier: '{args.target}'...")
    success = execute_download(
        target=args.target,
        models_dir=args.models_dir,
        force=args.force,
    )
    print("--------------------------------------------------")
    if success:
        print(f"{TAG_OK} Voice model setup complete.")
    else:
        print(f"{TAG_FAIL} One or more model downloads failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
