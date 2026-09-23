# Week 4 Milestone: Full Quiz Mode with Offline Neural Spanish & Mayan Voice

<div align="center">

| 🏠 [TutorBox](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 [Docs](../README.md) › [Milestones](roadmap.md) › **Week 4 Milestone** • **Related:** [Engineering Roadmap](roadmap.md) • [Voice Feedback Architecture](../architecture/voice-feedback.md) • [Session API Reference](../api/sessions.md)

</div>

---

This document summarizes the technical deliverables, architectural implementations, and quality metrics achieved during the **Week 4 Milestone** by **Student A (Pilot: Offline Neural Voice Pipeline)** and **Student B (Copilot: Classroom Display & Audio Triggering)**.

---

## 1. Executive Summary & Verification Metrics

* **Theme**: *"Voice Feedback: When the system speaks and when it stays silent"*
* **Status**: **Week 4 Milestone Complete & Green**
* **Backend Test Suite**: **876 / 876 passing tests** (comprehensive unit, runner isolation, benchmark, memory monitor, and end-to-end 10-round match simulation tests).
* **Statement Coverage**: **100.00% statement coverage** across all source code statements (`pyproject.toml` enforces `--cov-fail-under=80`).
* **Linter & Formatter**: **0 errors, 0 warnings** (`pre-commit run --all-files` clean across all 7 hooks).
* **Modularity Compliance**: **100% of production source files $\le 150$ LoC** and **100% of test files $\le 300$ LoC**, strictly validated by `tests/test_modularity_policy.py`.
* **Key Milestone Artifacts**:
  * **Pluggable Voice Architecture**: Hardware-agnostic `TTSBackend` protocol with Qwen3-TTS (GGUF via `llama-tts`) as the primary high-fidelity Spanish backend, Sherpa-ONNX and Piper VITS as lightweight neural fallbacks, Kokoro-82M opt-in, and `EspeakBackend` as the formant safety fallback, backed by a `TTSRouter` with 32-entry LRU cache.
  * **Primary-School Text Adaptation**: Oral fraction conversions, LaTeX sanitization, exponent reading, and natural sentence pacing (`core/tts/text.py`).
  * **Mayan Language Routing Seam**: Dedicated routing seam for Mayan K'iche' (`quc_Latn`) in `TTSRouter` with fail-safe error isolation (`503 Service Unavailable` when model checkpoint is absent).
  * **Multi-Engine Benchmarking & Accurate Preload Modeling**: Unified profiler (`tools/benchmark/tts/metrics.py`, `ab.py`, and `memory.py`) measuring cold load vs warm inference, Real-Time Factor (RTF), Host RAM, and GPU VRAM. In classroom quiz turns, TTS preloading during student voting yields pure neural generation: **2.290s warm p50** (0.2386x RTF, meeting the $\le 3.0$s SLA).
  * **Dual Memory Tracking (PC VRAM vs Jetson UMA)**: Background sampling (`MemoryMonitor`) capturing recursive child process working sets (`llama-tts.exe`) and GPU VRAM via NVML. Dynamic platform detection (`is_jetson_uma()`) accounts for Jetson Orin Nano's 8GB shared LPDDR5 DRAM architecture.
  * **Context Window Optimization**: Calibrated `TTS_QWEN_CONTEXT=1024` tokens, reclaiming ~325 MB of VRAM compared to 4096 without sacrificing classroom utterance quality.
  * **End-to-End 10-Round Match Suite**: Full match simulation (`test_session_10_round_speech.py`) proving deterministic >51% gating, bilingual dispatch, and first-press locking across 10 rounds.

---

## 2. Implemented Subsystems by Lead

### A. Student A (Pilot Scope: Offline Neural Voice Pipeline)

1. **Text Adaptation Layer for Primary-School Mathematics (`backend/src/core/tts/text.py`)**:
   * Mathematical fractions converted into natural classroom Spanish:
     * Oral fractions: $1/2 \to$ *"un medio"*, $2/3 \to$ *"dos tercios"*, $3/4 \to$ *"tres cuartos"*, $a/b \to$ *"a sobre b"*.
     * Exponents & roots: $x^2 \to$ *"x al cuadrado"*, $x^3 \to$ *"x al cubo"*.
     * Negative numbers: $-5 \to$ *"menos 5"*.
   * Stripping of residual LaTeX formatting (`\frac`, `$`, `\cdot`, `\pm`, `\le`, `\ge`, `\neq`) and markdown artifacts.
   * Natural sentence-ending boundary truncation (`.`, `!`, `?`) to enforce pedagogical conciseness bounded by `max_chars`.
2. **Typed Configuration & Hyperparameter Calibration (`backend/src/core/config/`)**:
   * Typed configuration parameters added to `TTSConfig`: `engine`, `piper_binary`, `piper_model_dir`, `piper_model_es`, `piper_speaker_es`, `piper_model_quc`, `piper_speaker_quc`, `piper_length_scale`, `piper_noise_scale`, `piper_noise_w_scale`.
   * Qwen3-TTS settings (`qwen_settings.py`): `binary_path`, `gguf_path`, `threads`, and `context_size = 1024` (saving ~325 MB VRAM).
   * Calibrated speech hyperparameters:
     * `length_scale = 1.12`: Slows delivery pace by 12% to facilitate comprehension for elementary students.
     * `noise_scale = 0.35`: Eliminates wobbly pitch artifacts, robotic warble, and acoustic peaking.
     * `noise_w_scale = 0.45`: Enforces steady, intelligible syllable cadence.
3. **Pluggable Voice Router & Multi-Engine Architecture (`backend/src/core/tts/`)**:
   * `protocols.py`: Formal `TTSBackend` protocol defining `synthesize()`, `is_available()`, `preload()`, and `unload()`.
   * `engines/qwen/`: Autoregressive neural voice powered by `llama-tts.exe` with GGUF weights. Separated into modular `engine.py` (146 LoC) and `runner.py` (62 LoC) to maintain strict $\le 150$ LoC compliance while capturing pure neural synthesis timings.
   * `engines/sherpa/`: Embedded Sherpa-ONNX VITS neural synthesis engine (`engine.py`, `models.py`) with token generation and sample conversion.
   * `engines/piper/`: High-fidelity neural synthesis using Piper VITS models on ONNX Runtime (`engine.py`, `models.py`) with automated `.onnx.json` config sanitization.
   * `engines/espeak/`: Formant synthesizer implementing `TTSBackend` protocol as ultra-lightweight fallback (`engine.py`, `cli.py`).
   * `router/`: Pluggable dispatcher (`router.py`, `selection.py`) selecting the Spanish tiers (`qwen3-tts`, `sherpa`, `piper`, `espeak`) in quality-first order, routing Mayan K'iche' (`quc_Latn`), falling back gracefully between Spanish tiers, and caching generated audio in an in-memory 32-entry LRU cache.
   * `api/session/speech.py`: Refactored to delegate synthesis directly to `core.tts.synthesize_speech()`.
4. **Empirical Multi-Engine Benchmark & Memory Profiling (`tools/benchmark/tts/`)**:
   * Unified benchmarking suite (`metrics.py`, `ab.py`) and memory tracking engine (`memory.py`):
     * Samples Host RAM across the full process tree (`proc.children(recursive=True)`).
     * Measures GPU VRAM using `ctypes` NVML bindings with PyTorch fallback.
     * Auto-detects NVIDIA Tegra hardware via `/etc/nv_tegra_release` to classify memory scope (`uma-unified`, `discrete-vram`, `host-only`).
   * Multi-Engine Comparison on Primary Math Benchmark Corpus:

| Engine | Provider | Cold Load | Warm p50 | RTF | Peak | Sample Rate | Memory Footprint |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| **Qwen3-TTS** | CUDA | 2,350.8 ms | **2.290 s** | **0.2386x** | 0.78 | 24,000 Hz | +2,976 MB RAM / +3,272 MB VRAM |
| **Sherpa-ONNX** | CPU | 2,154.1 ms | **0.388 s** | **0.0474x** | 0.78 | 22,050 Hz | +192 MB RAM / +2.8 MB VRAM |
| **Piper** | CPU | 1,998.6 ms | **0.405 s** | **0.0495x** | 0.78 | 22,050 Hz | +202 MB RAM / +15.8 MB VRAM |
| **Kokoro-82M** | CPU | 1,867.7 ms | **2.315 s** | **0.2781x** | 0.78 | 24,000 Hz | +488 MB RAM / +5.7 MB VRAM |
| **eSpeak-ng** | CPU | 86.3 ms | **0.325 s** | **0.0306x** | 0.78 | 22,050 Hz | +9.6 MB RAM / +0.5 MB VRAM |

   * See [Voice Feedback Architecture](../architecture/voice-feedback.md#7-empirical-latency--real-time-factor-benchmarks) for the daemon profiling run (Qwen 2.481 s / Sherpa 0.443 s / Piper 0.420 s) — same `<= 3.0 s` SLA verdict, variance from corpus length and hardware topology.

5. **Jetson Orin Nano 8GB Memory Architecture & Lifecycle Decoupling**:
   * Asynchronous lifecycle separation: question generation and speech synthesis do not execute concurrently.
   * Invoking `/api/v1/llm/unload` frees the ~4.7 GB SLM footprint before preloading Qwen3-TTS during the 20–30s student voting window, guaranteeing ~5.5 GB of free unified memory.
   * For continuous background operation without lifecycle swaps, Sherpa-ONNX (+192 MB) and Piper (+202 MB) provide high-quality fallback paths.
6. **End-to-End 10-Question Classroom Match Verification Suite (`test_session_10_round_speech.py`)**:
   * Full match simulation verifying deterministic >51% gating across 10 distinct rounds:
     * Round 1 (100% Distractor B): Speaks Spanish (`200 OK` + WAV).
     * Round 2 (60% Distractor C): Speaks Spanish (`200 OK` + WAV).
     * Round 3 (100% Correct A): Silent (`409 Conflict`, majority correct).
     * Round 4 (40% B, 40% C, 20% D): Silent (`409 Conflict`, tie between distractors).
     * Round 5 (60% Correct, 40% Wrong): Silent (`409 Conflict`).
     * Round 6 (50% / 50% split): Silent (`409 Conflict`).
     * Round 7 (0 votes / timeout): Silent (`409 Conflict`).
     * Round 8 (80% Distractor D): Speaks Mayan K'iche' (`200 OK` + WAV, `lang=quc`).
     * Round 9 (Duplicate vote attempt): First-press lock triggers `409 Conflict`, only first vote recorded, speaks B explanation (`200 OK`).
     * Round 10 (80% Distractor C): Final round verification, speaks Spanish (`200 OK` + WAV).

---

### B. Student B (Copilot Scope: Classroom Display & Audio Triggering)

1. **Classroom HDMI Screen (`pwa/pilas/pantalla/`)**:
   * Decoupled public display presenting real-time question text, countdown progress, and anonymized aggregate bar charts.
   * Answer-safe phase gating preventing answer leakage during voting windows.
2. **Audio Playback Triggering**:
   * Consumes `GET /api/v1/session/{id}/speech` upon round reveal when >51% triggers.
   * Handles browser audio context priming for seamless classroom speaker playback.

---

## 3. Tuesday Jury Defense Package (Copilot B Defense Script)

* **Topic**: *"Voice Feedback: When the system speaks and when it stays silent"*
* **Presenter**: Student B (Copilot)

### Key Talking Points for the Jury:

1. **Acoustic Architecture & Model Selection**:
   * Explain why **Qwen3-TTS** is the current quality winner, and why Sherpa-ONNX/Piper provide sub-second fallbacks while eSpeak-ng remains the robotic availability safety net.
   * Why Spanish Harvard Sentences (`es_ES-sharvard-medium`, Speaker 1) was selected as the educational default over Mexican regional voices (`es_MX-ald`, `es_MX-claude`): neutral, textbook-clean diction preventing regional bias in Central American classrooms.
2. **Deterministic >51% Gating (Targeted Intervention vs Narration)**:
   * Emphasize that TutorBox is **not a screen reader**: voice feedback is a targeted pedagogical intervention triggered strictly when $>51\%$ of the class share the exact same conceptual misconception:
     $$\frac{\text{distractor\_votes}}{\text{total\_votes}} > 0.51$$
   * Ties, dispersed wrong answers, majority correct, or exact 51.0% remain strictly silent to avoid classroom audio fatigue.
3. **Hardware Budget & Memory Co-Existence**:
   * Present the Jetson Orin Nano 8GB memory budget: co-existing comfortably with `llama.cpp` (4B model) inside 4.70 GB total RAM (41.2% safety margin).
4. **End-to-End Live Proof**:
   * Reference the 10-round classroom match simulation (`test_session_10_round_speech.py`) demonstrating consistent, deterministic gating across all 10 pedagogical scenarios.
