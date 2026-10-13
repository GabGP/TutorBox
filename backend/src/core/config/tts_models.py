"""TTS configuration data model for Utz'tutor edge appliance."""

from dataclasses import dataclass

from core.config.constants import (
    DEFAULT_TTS_AMPLITUDE,
    DEFAULT_TTS_BINARY,
    DEFAULT_TTS_ENABLED,
    DEFAULT_TTS_ENGINE,
    DEFAULT_TTS_KOKORO_MODEL_DIR,
    DEFAULT_TTS_KOKORO_MODEL_FILE,
    DEFAULT_TTS_KOKORO_PROVIDER,
    DEFAULT_TTS_KOKORO_SPEAKER_ID,
    DEFAULT_TTS_KOKORO_VOICE,
    DEFAULT_TTS_MAX_CHARS,
    DEFAULT_TTS_MELO_VOICE,
    DEFAULT_TTS_MOSS_MODEL,
    DEFAULT_TTS_PIPER_BINARY,
    DEFAULT_TTS_PIPER_LENGTH_SCALE,
    DEFAULT_TTS_PIPER_MODEL_DIR,
    DEFAULT_TTS_PIPER_MODEL_ES,
    DEFAULT_TTS_PIPER_MODEL_QUC,
    DEFAULT_TTS_PIPER_NOISE_SCALE,
    DEFAULT_TTS_PIPER_NOISE_W_SCALE,
    DEFAULT_TTS_PIPER_SPEAKER_ES,
    DEFAULT_TTS_PIPER_SPEAKER_QUC,
    DEFAULT_TTS_PITCH,
    DEFAULT_TTS_QWEN_BATCH,
    DEFAULT_TTS_QWEN_BINARY,
    DEFAULT_TTS_QWEN_CONTEXT,
    DEFAULT_TTS_QWEN_GGUF_PATH,
    DEFAULT_TTS_QWEN_SEED,
    DEFAULT_TTS_QWEN_SPEAKER_FILE,
    DEFAULT_TTS_QWEN_THREADS,
    DEFAULT_TTS_SHERPA_MODEL_ES,
    DEFAULT_TTS_SHERPA_PROVIDER,
    DEFAULT_TTS_SHERPA_THREADS,
    DEFAULT_TTS_TIMEOUT_SECONDS,
    DEFAULT_TTS_VOICE,
    DEFAULT_TTS_VOICE_QUC,
    DEFAULT_TTS_WORDS_PER_MINUTE,
)

__all__ = ["TTSConfig"]


@dataclass(frozen=True)
class TTSConfig:
    """Offline classroom voice with neural tiers and an eSpeak safety fallback."""

    enabled: bool = DEFAULT_TTS_ENABLED
    engine: str = DEFAULT_TTS_ENGINE
    binary: str = DEFAULT_TTS_BINARY
    voice: str = DEFAULT_TTS_VOICE
    voice_quc: str = DEFAULT_TTS_VOICE_QUC
    words_per_minute: int = DEFAULT_TTS_WORDS_PER_MINUTE
    pitch: int = DEFAULT_TTS_PITCH
    amplitude: int = DEFAULT_TTS_AMPLITUDE
    timeout_seconds: float = DEFAULT_TTS_TIMEOUT_SECONDS
    max_chars: int = DEFAULT_TTS_MAX_CHARS

    piper_binary: str = DEFAULT_TTS_PIPER_BINARY
    piper_model_dir: str = DEFAULT_TTS_PIPER_MODEL_DIR
    piper_model_es: str = DEFAULT_TTS_PIPER_MODEL_ES
    piper_speaker_es: int = DEFAULT_TTS_PIPER_SPEAKER_ES
    piper_model_quc: str = DEFAULT_TTS_PIPER_MODEL_QUC
    piper_speaker_quc: int = DEFAULT_TTS_PIPER_SPEAKER_QUC
    piper_length_scale: float = DEFAULT_TTS_PIPER_LENGTH_SCALE
    piper_noise_scale: float = DEFAULT_TTS_PIPER_NOISE_SCALE
    piper_noise_w_scale: float = DEFAULT_TTS_PIPER_NOISE_W_SCALE

    sherpa_model_es: str = DEFAULT_TTS_SHERPA_MODEL_ES
    sherpa_threads: int = DEFAULT_TTS_SHERPA_THREADS
    sherpa_provider: str = DEFAULT_TTS_SHERPA_PROVIDER
    moss_model: str = DEFAULT_TTS_MOSS_MODEL
    kokoro_voice: str = DEFAULT_TTS_KOKORO_VOICE
    kokoro_model_dir: str = DEFAULT_TTS_KOKORO_MODEL_DIR
    kokoro_model_file: str = DEFAULT_TTS_KOKORO_MODEL_FILE
    kokoro_speaker_id: int = DEFAULT_TTS_KOKORO_SPEAKER_ID
    kokoro_provider: str = DEFAULT_TTS_KOKORO_PROVIDER
    melo_voice: str = DEFAULT_TTS_MELO_VOICE
    qwen_binary: str = DEFAULT_TTS_QWEN_BINARY
    qwen_gguf_path: str = DEFAULT_TTS_QWEN_GGUF_PATH
    qwen_threads: int = DEFAULT_TTS_QWEN_THREADS
    qwen_context: int = DEFAULT_TTS_QWEN_CONTEXT
    qwen_batch: int = DEFAULT_TTS_QWEN_BATCH
    qwen_seed: int = DEFAULT_TTS_QWEN_SEED
    qwen_speaker_file: str = DEFAULT_TTS_QWEN_SPEAKER_FILE
