"""Standalone inference harness for the MeloTTS Spanish ONNX model."""

from __future__ import annotations

import gc
import importlib
import time
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from tools.benchmark.tts.audio.wav_encoding import encode_mono_pcm16_wav
from tools.benchmark.tts.melo.support_files import load_lexicon, load_token_ids
from tools.benchmark.tts.melo.tokenizer import text_to_token_ids as tokenize_text
from tools.benchmark.tts.shared import paths
from tools.benchmark.tts.shared.units import MILLISECONDS_PER_SECOND

if TYPE_CHECKING:
    from types import ModuleType

    import onnxruntime as ort

ONNX_RUNTIME_MODULE_NAME: str = "onnxruntime"

DEFAULT_SAMPLE_RATE: int = 44100
DEFAULT_SPEED: float = 1.0
MINIMUM_SPEED: float = 0.1
NOISE_SCALE: float = 0.667
NOISE_SCALE_W: float = 0.8
SPEAKER_ID: int = 0

MODEL_FILE_NAME: str = "model.onnx"
LEXICON_FILE_NAME: str = "lexicon.txt"
TOKENS_FILE_NAME: str = "tokens.txt"

CUDA_EXECUTION_PROVIDERS: list[str] = ["CUDAExecutionProvider", "CPUExecutionProvider"]
CPU_EXECUTION_PROVIDERS: list[str] = ["CPUExecutionProvider"]


class MeloTTSHarness:
    """Standalone inference harness for MeloTTS Spanish ONNX model."""

    def __init__(
        self,
        model_dir: Path | str | None = None,
        provider: str = "cpu",
    ) -> None:
        resolved_model_dir = paths.MELO_MODEL_DIR if model_dir is None else model_dir
        self.model_dir = Path(resolved_model_dir)
        self.provider = provider
        self.model_path = self.model_dir / MODEL_FILE_NAME
        self.lexicon_path = self.model_dir / LEXICON_FILE_NAME
        self.tokens_path = self.model_dir / TOKENS_FILE_NAME

        # Imported when a harness is built, not with this module: reading the
        # command line (--help) must not load the native runtime, which logs
        # host hardware warnings on some machines. Building the harness still
        # comes before the profiler's memory baseline and load timer, so
        # load_ms and rss_delta_mb keep measuring the model alone.
        self._onnx_runtime: ModuleType = importlib.import_module(
            ONNX_RUNTIME_MODULE_NAME
        )
        self._session: ort.InferenceSession | None = None
        self._token_ids_by_symbol: dict[str, int] = load_token_ids(self.tokens_path)
        self._lexicon: dict[str, list[str]] = load_lexicon(self.lexicon_path)

    def load(self) -> float:
        """Loads the ONNX runtime session and returns duration in ms."""
        start_time = time.perf_counter()
        providers = list(
            CUDA_EXECUTION_PROVIDERS
            if self.provider == "cuda"
            else CPU_EXECUTION_PROVIDERS
        )
        self._session = self._onnx_runtime.InferenceSession(
            str(self.model_path), providers=providers
        )
        elapsed_seconds = time.perf_counter() - start_time
        return elapsed_seconds * MILLISECONDS_PER_SECOND

    def unload(self) -> None:
        """Unloads the ONNX runtime session."""
        self._session = None
        gc.collect()

    def is_loaded(self) -> bool:
        """Returns True if the session is currently active in memory."""
        return self._session is not None

    def text_to_token_ids(self, text: str) -> list[int]:
        """Converts Spanish text into interspersed phoneme token sequence."""
        return tokenize_text(text, self._token_ids_by_symbol, self._lexicon)

    def synthesize(
        self,
        text: str,
        speed: float = DEFAULT_SPEED,
    ) -> bytes:
        """Synthesizes text into 16-bit mono 44.1 kHz WAV bytes."""
        if self._session is None:
            self.load()
        assert self._session is not None

        token_ids = self.text_to_token_ids(text)
        model_inputs = _build_model_inputs(token_ids, speed)
        outputs = self._session.run(None, model_inputs)
        # run() is typed as returning arrays, sparse tensors, lists or dicts; this
        # model's first output is always a dense audio array.
        audio_samples = np.asarray(outputs[0]).squeeze()
        return encode_mono_pcm16_wav(audio_samples, DEFAULT_SAMPLE_RATE)


def _build_model_inputs(token_ids: list[int], speed: float) -> dict[str, np.ndarray]:
    """Packs token ids and synthesis settings into the seven named model inputs."""
    token_matrix = np.array([token_ids], dtype=np.int64)
    token_counts = np.array([token_matrix.shape[1]], dtype=np.int64)
    tones = np.zeros_like(token_matrix, dtype=np.int64)
    speaker_ids = np.array([SPEAKER_ID], dtype=np.int64)
    noise_scale = np.array([NOISE_SCALE], dtype=np.float32)
    length_scale = np.array([1.0 / max(MINIMUM_SPEED, speed)], dtype=np.float32)
    noise_scale_w = np.array([NOISE_SCALE_W], dtype=np.float32)
    return {
        "x": token_matrix,
        "x_lengths": token_counts,
        "tones": tones,
        "sid": speaker_ids,
        "noise_scale": noise_scale,
        "length_scale": length_scale,
        "noise_scale_w": noise_scale_w,
    }
