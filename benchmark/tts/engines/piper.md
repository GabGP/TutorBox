# Piper TTS (Active Baseline)

## Architectural Profile
- **Architecture**: VITS (Conditional Variational Autoencoder with Adversarial Learning for End-to-End Text-to-Speech)
- **Model Checkpoint**: `es_ES-sharvard-medium.onnx` + `es_ES-sharvard-medium.onnx.json`
- **Default Speaker**: Speaker 1 (educator style, female Latin/Spanish standard)
- **License**: MIT
- **Sample Rate**: 22,050 Hz (16-bit mono PCM)
- **Memory Footprint**: ~60–80 MB model file, ~150–250 MB RAM resident
- **Measured Performance**:
  - Warm Latency: ~0.237 s
  - Real-Time Factor (RTF): 0.044x
  - Peak Amplitude: 0.78 (normalized)

## Integration Details
- In-memory execution via `piper-tts` Python library, with automatic fallback to subprocess CLI if the native C++ library fails.
- Multi-voice support: Spanish (`es`) and Mayan K'iche' (`quc_Latn-maya-medium.onnx`).
- Configurable speech parameters: `length_scale=1.12` (relaxed pedagogical cadence), `noise_scale=0.35`, `noise_w_scale=0.45`.
