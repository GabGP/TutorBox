"""Engine-name catalogue, Qwen alias and comma-list parsing for the TTS sweep."""

from __future__ import annotations

DEFAULT_SWEEP_ENGINES: str = "qwen3-tts,sherpa,piper,espeak"

SUPPORTED_ENGINES: frozenset[str] = frozenset(
    {"qwen3-tts", "sherpa", "piper", "espeak", "kokoro", "melo", "moss-nano"}
)
ENGINE_ALIASES: dict[str, str] = {"qwen": "qwen3-tts"}


def normalize_engine_name(name: str) -> str:
    """Returns the canonical benchmark name while retaining the short Qwen alias."""
    normalized = name.strip().lower()
    return ENGINE_ALIASES.get(normalized, normalized)


def parse_engine_names(raw: str) -> list[str]:
    """Normalizes, de-duplicates, and validates comma-separated engine names."""
    names = [normalize_engine_name(name) for name in raw.split(",") if name.strip()]
    unsupported = [name for name in names if name not in SUPPORTED_ENGINES]
    if unsupported:
        listed = ", ".join(dict.fromkeys(unsupported))
        raise ValueError(f"unsupported engine(s): {listed}; use qwen3-tts for Qwen")
    if not names:
        raise ValueError("--engines must contain at least one engine")
    return list(dict.fromkeys(names))
