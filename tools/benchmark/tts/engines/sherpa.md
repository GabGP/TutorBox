# Sherpa-ONNX Engine Profile (Secondary Neural Fallback)

## Architectural Profile

- **Runtime**: `sherpa-onnx` C++ runtime with ONNX Runtime execution providers.
- **Model**: Piper-compatible Spanish VITS checkpoint `es_ES-sharvard-medium.onnx`.
- **Hardware Target**: CPU by default, with optional CUDA provider selection.
- **License**: Apache 2.0 runtime and compatible model assets.
- **Thread Allocation**: Configurable with `TTS_SHERPA_THREADS` (default: 6).
- **Sample Rate**: 22,050 Hz, inherited from the Spanish VITS model.

## Empirical Benchmark Results (Math Corpus A/B)

The current first-corpus CSV reports:

- **Warm Latency (p50)**: **0.338 s** (`<= 3.0 s` classroom SLA).
- **Warm Latency (p95)**: **0.347 s**.
- **Real-Time Factor (RTF)**: **0.0413x**.
- **Normalized Peak Amplitude**: **0.78** (shared production calibration).
- **Memory Footprint (RSS Delta)**: **+188.38 MB**.
- **Audio Output**: 22,050 Hz 16-bit mono RIFF/WAV.

## Acoustic & Deployment Assessment

- Sherpa-ONNX and Piper use the same Spanish VITS checkpoint family, so their pronunciation and timbre are closely related.
- Sherpa keeps the model in a resident runtime object after preload, giving it a much faster repeated-synthesis path than the one-shot Qwen CLI.
- If CUDA initialization fails, the backend falls back to CPU and the benchmark provider must report the resolved provider, not merely the requested one.

## Spike Decision

* **Status**: **APPROVED AS THE SECONDARY SPANISH TIER** (`TTS_ENGINE=sherpa`).
* **Evaluation Verdict**: Use after Qwen3-TTS for speed, low resource use, and predictable classroom latency.
