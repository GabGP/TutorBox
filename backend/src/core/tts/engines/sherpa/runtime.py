"""Runtime loader and execution provider management for Sherpa-ONNX."""

import logging
import os
import sys
from pathlib import Path
from typing import Any

from core.config.models import TTSConfig
from core.tts.engines.provider import resolve_execution_provider
from core.tts.exceptions import TTSUnavailableError

logger = logging.getLogger(__name__)


def ensure_ort_dll_directory() -> None:
    """Registers onnxruntime/capi on Windows to prevent loading system DLLs."""
    if sys.platform != "win32":
        return
    try:
        import onnxruntime

        ort_capi = Path(onnxruntime.__file__).parent / "capi"
        if ort_capi.is_dir():
            os.add_dll_directory(str(ort_capi))
    except (ImportError, OSError, AttributeError) as err:
        logger.debug("Could not register onnxruntime DLL directory: %s", err)


def create_offline_tts(
    model_path: Path,
    tokens_path: Path,
    data_dir: Path,
    tts_cfg: TTSConfig,
) -> Any:
    """Initializes Sherpa-ONNX OfflineTts with CUDA provider, falling back to CPU."""
    try:
        import sherpa_onnx
    except ImportError as err:
        raise TTSUnavailableError("sherpa-onnx runtime is not installed.") from err

    vits_cfg = sherpa_onnx.OfflineTtsVitsModelConfig(
        model=str(model_path),
        tokens=str(tokens_path),
        data_dir=str(data_dir),
        length_scale=tts_cfg.piper_length_scale,
        noise_scale=tts_cfg.piper_noise_scale,
        noise_scale_w=tts_cfg.piper_noise_w_scale,
    )
    provider = resolve_execution_provider(tts_cfg.sherpa_provider)
    try:
        model_config = sherpa_onnx.OfflineTtsModelConfig(
            vits=vits_cfg,
            num_threads=tts_cfg.sherpa_threads,
            provider=provider,
        )
        return sherpa_onnx.OfflineTts(
            sherpa_onnx.OfflineTtsConfig(model=model_config)
        )
    except Exception as err:
        if provider == "cuda":
            logger.info("Sherpa CUDA init unavailable; falling back to CPU: %s", err)
            try:
                model_config = sherpa_onnx.OfflineTtsModelConfig(
                    vits=vits_cfg,
                    num_threads=tts_cfg.sherpa_threads,
                    provider="cpu",
                )
                return sherpa_onnx.OfflineTts(
                    sherpa_onnx.OfflineTtsConfig(model=model_config)
                )
            except Exception as cpu_err:
                raise TTSUnavailableError(
                    f"Failed to initialize Sherpa-ONNX on CPU: {cpu_err}"
                ) from cpu_err
        raise TTSUnavailableError(f"Failed to initialize Sherpa-ONNX: {err}") from err
