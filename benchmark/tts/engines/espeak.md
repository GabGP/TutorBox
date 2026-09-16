# eSpeak-ng Engine Profile (Ultimate Fallback)

## Architectural Profile

- **Architecture**: Rule-based formant synthesis.
- **Runtime**: `espeak-ng` or the legacy `espeak` command-line executable.
- **Model Footprint**: No neural model weights; the voice data is installed with the executable.
- **Hardware Target**: CPU-only; no accelerator or Python model dependency is required.
- **Language Role**: Spanish fallback only unless a compatible installed voice is explicitly configured.

## Empirical Benchmark Results

The current first-corpus CSV reports approximately `0.215 s` warm p50, `0.0203x` RTF, `22,050 Hz`, and a pre-calibration peak of `1.00`. Production output is now linearly calibrated to the shared `0.78` target before it is returned to the API.

## Acoustic & Deployment Assessment

- **Strengths**: Extremely small footprint, immediate startup, predictable CPU behavior, and broad installation availability.
- **Trade-off**: The formant voice is intentionally robotic and metallic. It is a safety net for availability, not the classroom-quality default.
- **Configuration**: `TTS_ESPEAK_BINARY`, `TTS_VOICE`, `TTS_WORDS_PER_MINUTE`, `TTS_PITCH`, and `TTS_AMPLITUDE`.

## Spike Decision

* **Status**: **RETAINED AS THE ULTIMATE FALLBACK**.
* **Router Role**: Used after Qwen3-TTS, Sherpa-ONNX, and Piper are unavailable or fail during Spanish synthesis.
