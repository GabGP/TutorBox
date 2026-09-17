# Qwen3-TTS Engine Profile (Primary Neural Voice)

## Architectural Profile

- **Model**: `Qwen3-TTS-12Hz-1.7B-Base`, quantized to GGUF `Q4_K_M` for local inference.
- **Architecture**: 1.7B autoregressive speech model paired with a 12 Hz neural audio codec/vocoder.
- **Runtime**: `llama-tts` from `llama.cpp` tools, offloading all layers to GPU (`-ngl 99`).
- **Target Language**: Spanish (`--tts-lang es`).
- **Sample Rate**: 24,000 Hz, 16-bit mono PCM WAV.
- **Model Assets**: `Qwen3-TTS-12Hz-1.7B-Base-Q4_K_M.gguf` (1.1 GB) plus `mmproj-Qwen3-TTS-12Hz-1.7B-Base-Q8_0.gguf` (425 MB).
- **Context Allocation**: Default `TTS_QWEN_CONTEXT=1024` (~350 MB VRAM savings compared to 4096).

---

## Empirical Benchmark Results (Math Intervention Corpus)

Evaluated on the standardized classroom math intervention corpus entry (`corpus/es_math.txt`):

| Metric | Measured Value | SLA Target | Status |
| :--- | :---: | :---: | :---: |
| **Provider** | `cuda` | Hardware CUDA execution | **CONFIRMED** |
| **Cold First Latency** | 4.851 s | `<= 15.0 s` | **PASS** |
| **Model Preload / Load** | 2,350.80 ms | Preloadable during voting | **PASS** |
| **Warm Latency (p50)** | **2.290 s** | `<= 3.0 s` | **PASS** |
| **Warm Latency (p95)** | **2.340 s** | `<= 3.5 s` | **PASS** |
| **Real-Time Factor (RTF)** | **0.2386x** | `< 0.50x` (4.19x realtime) | **PASS** |
| **Audio Duration** | 9.04 s | Natural pedagogical pacing | **PASS** |
| **Sample Rate** | 24,000 Hz | Native model frequency | **PASS** |
| **Peak Amplitude** | **0.78** | `0.70 .. 0.85` | **PASS** (Calibrated) |
| **Peak Host RAM (RSS)** | 2,976.12 MB | Process tree working set | Measured |
| **Peak Device VRAM** | 3,272.18 MB | CUDA GPU device memory | Measured |
| **Memory Scope** | `discrete-vram` | Discrete VRAM on workstation | Dual-Tracked |

---

## Asynchronous Lifecycle & Pedagogical Preload Timing

In the TutorBox appliance architecture:
1. **Asynchronous SLM vs TTS Lifecycle**: Question generation by the Small Language Model (SLM) is asynchronous to quiz execution. Before student voting begins, the SLM is unloaded (`/api/v1/llm/unload`), reclaiming ~4.7 GB of memory.
2. **Preloading During Voting**: When the teacher launches a quiz round, students vote for 20–30 seconds. The appliance preloads the neural TTS model during this voting period (`/api/v1/tts/load`).
3. **Warm Pedagogical Intervention**: If the >51% distractor rule triggers at the end of the round, the model weights and CUDA graph are already resident. The system only performs prompt evaluation, token generation, and vocoding (**2.29s warm latency**, RTF 0.2386x), satisfying the `<= 3.0s` classroom turnaround SLA with high margin.

---

## Memory Architecture: Discrete PC vs Jetson Orin Nano (UMA)

1. **Discrete GPU Workstation**:
   - Host RAM and GPU VRAM are physically separate.
   - Host RSS reflects the memory-mapped GGUF files in the process address space (~2.9 GB), while GPU VRAM tracks tensor weights and CUDA computation buffers (~3.27 GB).
2. **NVIDIA Jetson Orin Nano (Unified Memory Architecture - UMA)**:
   - CPU and GPU share the identical **8 GB LPDDR5 physical memory pool**.
   - Allocating ~3.27 GB for Qwen3-TTS consumes ~40% of the entire appliance memory.
   - **Deployment Recommendation**: On Jetson, Qwen3-TTS is recommended as an opt-in primary voice when running independently of other heavy GPU tasks. When operating alongside resident services, **Sherpa-ONNX** (`0.388s warm`, `191 MB RAM`, `host-only`) serves as the ultra-lean secondary neural fallback.
