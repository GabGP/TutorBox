"""Typed domain configuration data models for TutorBox."""

from dataclasses import dataclass

from core.config.constants import (
    DEFAULT_AUTH_LOCKOUT_SECONDS,
    DEFAULT_AUTH_MAX_ATTEMPTS,
    DEFAULT_AUTH_MAX_TRACKED_KEYS,
    DEFAULT_BCRYPT_ROUNDS,
    DEFAULT_BUSY_TIMEOUT_MS,
    DEFAULT_CAPTIVE_PORTAL_ENABLED,
    DEFAULT_CAPTIVE_PORTAL_URL,
    DEFAULT_DB_PATH,
    DEFAULT_QUIZ_MAX_RETRIES,
    DEFAULT_SEED_TEACHER_PIN,
    DEFAULT_SEED_TEACHER_USERNAME,
    DEFAULT_SIGNUP_MAX_EVENTS,
    DEFAULT_SIGNUP_WINDOW_SECONDS,
    DEFAULT_SLM_BASE_URL,
    DEFAULT_SLM_MODEL_NAME,
    DEFAULT_SLM_TEMPERATURE,
    DEFAULT_SLM_TIMEOUT_SECONDS,
    DEFAULT_TTS_AMPLITUDE,
    DEFAULT_TTS_BINARY,
    DEFAULT_TTS_ENABLED,
    DEFAULT_TTS_ENGINE,
    DEFAULT_TTS_KOKORO_MODEL_DIR,
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
    DEFAULT_TTS_QWEN_GGUF_PATH,
    DEFAULT_TTS_QWEN_THREADS,
    DEFAULT_TTS_SHERPA_MODEL_ES,
    DEFAULT_TTS_SHERPA_PROVIDER,
    DEFAULT_TTS_SHERPA_THREADS,
    DEFAULT_TTS_TIMEOUT_SECONDS,
    DEFAULT_TTS_VOICE,
    DEFAULT_TTS_VOICE_QUC,
    DEFAULT_TTS_WORDS_PER_MINUTE,
)


@dataclass(frozen=True)
class DatabaseConfig:
    database_path: str = DEFAULT_DB_PATH
    busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS


@dataclass(frozen=True)
class SecurityConfig:
    bcrypt_rounds: int = DEFAULT_BCRYPT_ROUNDS
    auth_max_attempts: int = DEFAULT_AUTH_MAX_ATTEMPTS
    auth_lockout_seconds: int = DEFAULT_AUTH_LOCKOUT_SECONDS
    auth_max_tracked_keys: int = DEFAULT_AUTH_MAX_TRACKED_KEYS
    signup_max_events: int = DEFAULT_SIGNUP_MAX_EVENTS
    signup_window_seconds: int = DEFAULT_SIGNUP_WINDOW_SECONDS
    seed_teacher_username: str = DEFAULT_SEED_TEACHER_USERNAME
    seed_teacher_pin: str = DEFAULT_SEED_TEACHER_PIN


@dataclass(frozen=True)
class LLMConfig:
    base_url: str = DEFAULT_SLM_BASE_URL
    model_name: str = DEFAULT_SLM_MODEL_NAME
    temperature: float = DEFAULT_SLM_TEMPERATURE
    timeout_seconds: float = DEFAULT_SLM_TIMEOUT_SECONDS


@dataclass(frozen=True)
class QuizConfig:
    max_retries: int = DEFAULT_QUIZ_MAX_RETRIES


@dataclass(frozen=True)
class TTSConfig:
    """Offline classroom voice (Neural Piper + Formant eSpeak fallback)."""

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

    # Neural Piper configuration
    piper_binary: str = DEFAULT_TTS_PIPER_BINARY
    piper_model_dir: str = DEFAULT_TTS_PIPER_MODEL_DIR
    piper_model_es: str = DEFAULT_TTS_PIPER_MODEL_ES
    piper_speaker_es: int = DEFAULT_TTS_PIPER_SPEAKER_ES
    piper_model_quc: str = DEFAULT_TTS_PIPER_MODEL_QUC
    piper_speaker_quc: int = DEFAULT_TTS_PIPER_SPEAKER_QUC
    piper_length_scale: float = DEFAULT_TTS_PIPER_LENGTH_SCALE
    piper_noise_scale: float = DEFAULT_TTS_PIPER_NOISE_SCALE
    piper_noise_w_scale: float = DEFAULT_TTS_PIPER_NOISE_W_SCALE

    # Candidate engine configuration for A/B benchmarking
    sherpa_model_es: str = DEFAULT_TTS_SHERPA_MODEL_ES
    sherpa_threads: int = DEFAULT_TTS_SHERPA_THREADS
    sherpa_provider: str = DEFAULT_TTS_SHERPA_PROVIDER
    moss_model: str = DEFAULT_TTS_MOSS_MODEL
    kokoro_voice: str = DEFAULT_TTS_KOKORO_VOICE
    kokoro_model_dir: str = DEFAULT_TTS_KOKORO_MODEL_DIR
    kokoro_speaker_id: int = DEFAULT_TTS_KOKORO_SPEAKER_ID
    kokoro_provider: str = DEFAULT_TTS_KOKORO_PROVIDER
    melo_voice: str = DEFAULT_TTS_MELO_VOICE
    qwen_gguf_path: str = DEFAULT_TTS_QWEN_GGUF_PATH
    qwen_threads: int = DEFAULT_TTS_QWEN_THREADS


@dataclass(frozen=True)
class CaptivePortalConfig:
    """Where phone captive-portal probes are redirected when a device joins the AP."""

    enabled: bool = DEFAULT_CAPTIVE_PORTAL_ENABLED
    redirect_url: str = DEFAULT_CAPTIVE_PORTAL_URL


@dataclass(frozen=True)
class Settings:
    database: DatabaseConfig
    security: SecurityConfig
    llm: LLMConfig
    quiz: QuizConfig
    tts: TTSConfig
    captive_portal: CaptivePortalConfig
