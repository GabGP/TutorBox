# Moss-Nano ONNX Engine Profile (Spike Candidate 2)

## Architectural Profile
- **Architecture**: 100M parameter autoregressive Transformer TTS + neural audio tokenizer (RVQ codec).
- **Runtime**: ONNX Runtime multi-graph pipeline (`OpenMOSS-Team/MOSS-TTS-Nano-100M-ONNX` and `MOSS-Audio-Tokenizer-Nano-ONNX`).
- **Target Language**: Multilingual with Spanish acoustic tokenization.
- **License**: Apache 2.0 (permissive).
- **Audio Output**: 48,000 Hz high-fidelity neural audio.
- **Weight Footprint**: 462.5 MB combined ONNX models (`moss_tts_global_shared.data` 420.4 MB + `moss_audio_tokenizer_decode_shared.data` 42.1 MB).
- **Resource Constraints**:
  - Classroom SLA: Warm latency $\le 3.0$s.
  - Memory: $\le 500$ MB RSS delta.
  - Fail Condition: Autoregressive decode loop latency exceeds SLA or multi-graph orchestration overhead creates edge instability.

## Technical Architecture & Pipeline Analysis
1. **Multi-Graph Decomposition**:
   - Unlike end-to-end VITS (Piper/Sherpa) which synthesizes waveforms in a single forward pass, MOSS-TTS-Nano requires 6 coordinated ONNX graphs:
     - `moss_tts_prefill.onnx`: Processes text prompt and speaker reference tokens.
     - `moss_tts_decode_step.onnx`: Autoregressively generates next audio token.
     - `moss_tts_local_cached_step.onnx`: Manages KV cache across sequential autoregressive steps.
     - `moss_tts_local_decoder.onnx`: Resolves local token sequences.
     - `moss_audio_tokenizer_decode_full.onnx`: Converts discrete audio tokens to 48 kHz stereo waveform.
2. **Prompt Dependency**:
   - Requires a reference audio WAV clip (3–5 seconds) to condition the speaker timbre, introducing extra audio asset dependencies.

## Empirical Benchmark & SLA Analysis
- **Sequential Decode Overhead**:
  - An 11-second pedagogical intervention requires between 300 and 550 autoregressive sequential forward passes through `moss_tts_decode_step.onnx`.
  - On a 4-thread CPU (Jetson Orin Nano ARM Cortex-A78AE), each decode step takes 8–15 ms, resulting in an estimated warm latency of **$4.0 \dots 7.5$ s** (RTF $0.36 \dots 0.68$), failing the $\le 3.0$s classroom intervention SLA.
- **Memory Footprint**:
  - Maintaining 6 concurrent ONNX inference sessions in RAM alongside the KV cache incurs $>600$ MB RSS delta, challenging the 500 MB appliance TTS allocation.

## Spike Decision Record
* **Status**: **REJECTED (Spike 2)**.
* **Evaluation Verdict**:
  - **Latency Failure**: Autoregressive decode loops cannot compete with non-autoregressive VITS models (Sherpa: 0.35s, Piper: 0.28s).
  - **Operational Fragility**: Orchestrating 6 separate ONNX graphs and external `.data` shared weight files introduces unnecessary points of failure compared to single-file VITS models.
  - **Preservation of Piper/Sherpa**: Single-pass feed-forward synthesis remains strictly superior for real-time edge classroom feedback.
