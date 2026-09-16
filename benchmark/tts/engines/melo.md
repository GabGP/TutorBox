# MeloTTS Spanish Engine Profile (Spike Candidate 4)

## Architectural Profile
- **Architecture**: Multi-lingual VITS variant with speed control and Spanish acoustic checkpoint.
- **Runtime**: Evaluated via standalone ONNX Runtime harness (`benchmark/tts/harness_melo.py`) using `MiaoMint/MeloTTS-ONNX` Spanish export.
- **Target Language**: Spanish (`ES`).
- **License**: MIT
- **Model Checkpoint**: 170.6 MB ONNX export, 44.1 kHz sampling rate.
- **Resource Constraints**:
  - Warm Latency SLA: $\le 3.0$s.
  - Fail Condition: Exceeds warm latency budget (> 3.0s), introduces dependency conflicts with edge Linux distribution, or suffers from missing G2P lexicon entries.

## Empirical Benchmark Results (Workstation CPU 4-Thread)
- **Cold First Turn**: **5.396 s** (model load: 3,476.11 ms, synthesis: 1.920 s).
- **Warm Latency (p50)**: **2.061 s** ($\le 3.0$s classroom SLA satisfied).
- **Warm Latency (p95)**: **2.138 s** (low jitter across repeated invocations).
- **Real-Time Factor (RTF)**: **0.1871** (synthesizes 5.3x faster than real-time playback).
- **Audio Output**: 44,100 Hz 16-bit mono RIFF/WAV.
- **Normalized Peak Amplitude**: **0.611** (slightly lower gain than Piper/Sherpa 0.78 target).
- **Memory Footprint (RSS Delta)**: **+450.15 MB**.
- **Generated Audio Artifact**: `benchmark/tts/results/out/melo_es_0.wav` (949.0 KB, 11.018s duration).

## Findings & Pilot Trade-offs
1. **Acoustic Fidelity**: The 44.1 kHz output produces high-frequency clarity and expressive prosody, noticeably brighter than 22.05 kHz VITS baselines.
2. **SLA Compliance**: At 2.06s warm p50 (RTF 0.187), MeloTTS passes the $\le 3.0$s SLA on 4-thread CPU, though it is roughly 6x slower than Sherpa-ONNX (0.35s) and Piper (0.28s).
3. **G2P & Lexicon Fragility (Critical Finding)**:
   - Official PyTorch MeloTTS requires heavy dependencies (`torch`, `torchaudio`, `transformers`, `gruut`, `librosa`), conflicting with the lean edge runtime budget.
   - The standalone ONNX export relies on a static 9,200-word lexicon. Critical Spanish mathematical and diagnostic terms (`numerador`, `cuartos`, `denominadores`, `dividiste`, digits `100`, `2`, `5`) were absent from the base lexicon, requiring manual phonetic overrides.
   - Without an integrated runtime phonemizer (like `espeak-ng` in Piper/Sherpa/Kokoro), MeloTTS cannot dynamically synthesize arbitrary educational terms reliably.
4. **Architectural Recommendation for Pilot**:
   - **Reject for core classroom production**: The lack of an embedded, offline G2P phonemizer in the ONNX export creates fragility for dynamic quiz feedback.
   - Use Qwen3-TTS as the primary voice and Sherpa-ONNX/Piper as the production speed fallbacks.
