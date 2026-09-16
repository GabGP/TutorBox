"""Audio encoding, normalization, and hardware constants for TutorBox TTS."""

# Linear PCM Audio Format
PCM_CHANNELS_MONO: int = 1
PCM_SAMPLE_WIDTH_BYTES: int = 2  # 16-bit linear PCM (2 bytes per sample)
PCM_16BIT_MAX_AMPLITUDE: int = 32767
PCM_16BIT_MAX_FLOAT: float = 32768.0

# Normalized Audio Bounds (-1.0 to +1.0)
MIN_AUDIO_SAMPLE: float = -1.0
MAX_AUDIO_SAMPLE: float = 1.0
DEFAULT_TARGET_PEAK_AMPLITUDE: float = 0.78

# Unit Conversions
MILLISECONDS_PER_SECOND: float = 1000.0
BYTES_PER_KILOBYTE: int = 1024
BYTES_PER_MEGABYTE: float = 1024.0 * 1024.0

# Standard Sample Rates (Hz)
DEFAULT_PIPER_SAMPLE_RATE_HZ: int = 22050
DEFAULT_KOKORO_SAMPLE_RATE_HZ: int = 24000

# Subprocess & Runtime Defaults
DEFAULT_SPEECH_SPEED: float = 1.0
SUBPROCESS_SUCCESS_EXIT_CODE: int = 0
