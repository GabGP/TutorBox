# Piper TTS (Tertiary Neural Baseline)

## Architectural Profile

- **Architecture**: VITS (Conditional Variational Autoencoder with Adversarial Learning for end-to-end text-to-speech).
- **Model Checkpoint**: `es_ES-sharvard-medium.onnx` plus its JSON configuration.
- **Default Speaker**: Speaker 1 (Spanish educator profile).
- **License**: MIT.
- **Sample Rate**: 22,050 Hz (16-bit mono PCM).
- **Memory Footprint**: Approximately 150--250 MB resident, depending on runtime and model loading.

## Empirical Benchmark Results

The current first-corpus CSV reports approximately **0.274 s** warm p50, **0.0334x** RTF, and 22,050 Hz output. New production output is calibrated to a **0.78** peak so Piper is comparable with Sherpa-ONNX and Qwen3-TTS.

## Integration Details

- In-memory execution uses the `piper-tts` Python library, with a subprocess fallback if native synthesis fails.
- `TTS_PIPER_LENGTH_SCALE=1.12`, `TTS_PIPER_NOISE_SCALE=0.35`, and `TTS_PIPER_NOISE_W_SCALE=0.45` provide a calm educational cadence.
- Spanish is the tertiary neural fallback after Qwen3-TTS and Sherpa-ONNX. The same backend also retains the K'iche' model slot for `lang=quc`.

## Spike Decision

* **Status**: **RETAINED AS THE FAST TERTIARY FALLBACK** (`TTS_ENGINE=piper`).
* **Evaluation Verdict**: Excellent latency and low resource use; Sherpa-ONNX is preferred when both are installed because its resident runtime is easier to keep warm.
