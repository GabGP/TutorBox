# Sherpa-ONNX Engine Profile (Spike Candidate 1)

## Architectural Profile
- **Runtime**: `sherpa-onnx` C++ runtime with ONNX Runtime backend and ARM NEON / Jetson Linux aarch64 wheels.
- **Model Compatibility**:
  1. Piper VITS models (`es_ES-sharvard-medium.onnx`, `tokens.txt`, `espeak-ng-data`).
  2. Supertonic / Matcha-TTS Spanish models.
- **License**: Apache 2.0
- **Resource Constraints**:
  - Fail Condition: Warm latency > 3.0s or RSS delta > 500 MB.
  - Thread Allocation: Configurable (default 2–4 CPU threads on Jetson).

## Evaluation Focus
- Measures whether `sherpa-onnx` can run the existing Piper Sharvard model with lower latency and lower memory overhead compared to `piper-tts`.
- Test multi-threaded CPU execution stability under concurrent quiz turn processing.
