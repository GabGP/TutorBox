"""Espeak-ng phonemes for the engines that run on sherpa-onnx (Sherpa and Kokoro).

sherpa-onnx 2.0 no longer bundles espeak-ng: it ignores ``data_dir`` and gives
no audio for Piper voices or Spanish Kokoro text unless the caller passes the
phonemes in. piper-tts already ships espeak-ng, so the phonemes come from it.
espeak-ng keeps one voice for the whole process, so the call takes the same
lock and phonemizer as PiperVoice, which keeps it safe beside the Piper engine.
"""

from typing import Any

from core.tts.exceptions import TTSUnavailableError

__all__ = ["phoneme_generation_config", "phonemize_to_codepoints"]


def phonemize_to_codepoints(text: str, espeak_voice: str) -> list[list[int]]:
    """Returns the text's espeak-ng phonemes as codepoints, one list per sentence."""
    try:
        from piper import voice as piper_voice
        from piper.phonemize_espeak import EspeakPhonemizer
    except ImportError as err:
        raise TTSUnavailableError(
            "piper-tts, which provides the espeak-ng phonemizer, is not installed."
        ) from err

    with piper_voice._ESPEAK_PHONEMIZER_LOCK:
        if piper_voice._ESPEAK_PHONEMIZER is None:
            piper_voice._ESPEAK_PHONEMIZER = EspeakPhonemizer()
        sentences = piper_voice._ESPEAK_PHONEMIZER.phonemize(espeak_voice, text)
    return [[ord(phoneme) for phoneme in sentence] for sentence in sentences]


def phoneme_generation_config(
    text: str, espeak_voice: str, speaker_id: int, speed: float = 1.0
) -> Any:
    """Builds the sherpa-onnx GenerationConfig that speaks the text's phonemes."""
    import sherpa_onnx

    config = sherpa_onnx.GenerationConfig()
    config.sid = speaker_id
    config.speed = speed
    config.phoneme_codepoints = phonemize_to_codepoints(text, espeak_voice)
    return config
