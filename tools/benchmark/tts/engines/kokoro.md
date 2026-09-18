# Kokoro-ES Engine Profile (Spike Candidate 3)

## Architectural Profile
- **Architecture**: 82M parameter StyleTTS2 variant (multilingual v1.0).
- **Runtime**: `sherpa-onnx` C++ edge runtime with `OfflineTtsKokoroModelConfig`.
- **Model Checkpoint**: `csukuangfj/kokoro-int8-multi-lang-v1_0` (114 MB INT8 ONNX, 28 MB voice embeddings).
- **Target Language / Speaker**: Spanish (`em_santa`, speaker ID 53).
- **G2P Dependency**: Bundled `espeak-ng-data` phonemization pipeline.
- **License**: Apache 2.0.

## Empirical Benchmark Results (Workstation CPU 4-Thread)
- **Cold First Turn**: 9.838 s (model load: 1423.95 ms)
- **Warm Latency (p50)**: 8.296 s
- **Warm Latency (p95)**: 8.324 s
- **Real-Time Factor (RTF)**: 0.9045
- **RAM Footprint (RSS Delta)**: +323.42 MB
- **Sample Rate**: 24,000 Hz
- **Calibrated Peak Amplitude**: 0.78
- **Generated Audio Artifact**: `tools/benchmark/tts/results/out/kokoro_es_0.wav`

## Findings & Pilot Trade-offs
1. **Prosodic Naturalness**: Kokoro-82M delivers rich, conversational Spanish prosody at 24 kHz, with fluid pitch contours compared to VITS.
2. **CPU Inference Latency**: At 8.30s on CPU (RTF 0.905), Kokoro on CPU fails the classroom SLA threshold ($\le 3.0$s) for rapid turn-taking.
3. **GPU / CUDA Acceleration**: To meet the $\le 3.0$s SLA in production, Kokoro requires CUDA execution provider (`provider="cuda"` via GPU-enabled ONNX runtime build on Jetson Orin Nano).
4. **Memory Footprint**: +323 MB is lightweight and fits comfortably alongside the local SLM lifecycle management.
