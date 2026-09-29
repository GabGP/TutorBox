"""Settings for Mode 2, the Socratic math tutor (see modes/socratic).

Kept out of the shared Settings aggregate: the tutor talks to the same completion
server as the quiz generator (SLM_BASE_URL) but with its own model and limits.
"""

import os
from dataclasses import dataclass

from core.config.parsers import parse_float, parse_int

__all__ = [
    "DEFAULT_TUTOR_MODEL_NAME",
    "TutorConfig",
    "load_tutor_config",
]

# Ollama name for bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF at Q8_0.
DEFAULT_TUTOR_MODEL_NAME = "hf.co/bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF:Q8_0"
# DeepSeek recommends 0.5-0.7 for its R1 distills.
DEFAULT_TUTOR_TEMPERATURE = 0.6
# The distill always reasons first (~100-300 tokens) before the short reply.
DEFAULT_TUTOR_MAX_TOKENS = 768
DEFAULT_TUTOR_TIMEOUT_SECONDS = 45.0
DEFAULT_TUTOR_MAX_CONCURRENT = 2
DEFAULT_TUTOR_QUEUE_SECONDS = 20.0
DEFAULT_TUTOR_TURNS_PER_MINUTE = 12


@dataclass(frozen=True)
class TutorConfig:
    model_name: str = DEFAULT_TUTOR_MODEL_NAME
    temperature: float = DEFAULT_TUTOR_TEMPERATURE
    max_tokens: int = DEFAULT_TUTOR_MAX_TOKENS
    timeout_seconds: float = DEFAULT_TUTOR_TIMEOUT_SECONDS
    max_concurrent: int = DEFAULT_TUTOR_MAX_CONCURRENT
    queue_seconds: float = DEFAULT_TUTOR_QUEUE_SECONDS
    turns_per_minute: int = DEFAULT_TUTOR_TURNS_PER_MINUTE


def load_tutor_config() -> TutorConfig:
    """Reads TUTOR_* from the environment; invalid or out-of-range values fall back."""
    return TutorConfig(
        model_name=(os.environ.get("TUTOR_MODEL_NAME") or "").strip()
        or DEFAULT_TUTOR_MODEL_NAME,
        temperature=parse_float(
            "TUTOR_TEMPERATURE", DEFAULT_TUTOR_TEMPERATURE, 0.0, 2.0
        ),
        max_tokens=parse_int("TUTOR_MAX_TOKENS", DEFAULT_TUTOR_MAX_TOKENS, 64, 4096),
        timeout_seconds=parse_float(
            "TUTOR_TIMEOUT_SECONDS", DEFAULT_TUTOR_TIMEOUT_SECONDS, 1.0, 600.0
        ),
        max_concurrent=parse_int(
            "TUTOR_MAX_CONCURRENT", DEFAULT_TUTOR_MAX_CONCURRENT, 1, 16
        ),
        queue_seconds=parse_float(
            "TUTOR_QUEUE_SECONDS", DEFAULT_TUTOR_QUEUE_SECONDS, 0.0, 300.0
        ),
        turns_per_minute=parse_int(
            "TUTOR_TURNS_PER_MINUTE", DEFAULT_TUTOR_TURNS_PER_MINUTE, 1, 120
        ),
    )
