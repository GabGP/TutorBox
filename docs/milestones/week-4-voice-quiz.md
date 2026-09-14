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
* **Backend Test Suite**: **725 / 725 passing tests** (32 new unit, benchmark, profiler, and end-to-end 10-round match simulation tests added).
* **Statement Coverage**: **100.00% statement coverage** across all source code statements (`pyproject.toml` enforces `--cov-fail-under=80`).
* **Linter & Formatter**: **0 errors, 0 warnings** (`pre-commit run --all-files` clean across all 7 hooks).
* **Modularity Compliance**: **100% of production source files $\le 150$ LoC** and **100% of test files $\le 300$ LoC**, strictly validated by `tests/test_modularity_policy.py`.
* **Key Milestone Artifacts**:
  * **Pluggable Voice Architecture**: Hardware-agnostic `TTSBackend` protocol with in-memory `PiperBackend` (ONNX VITS), `EspeakBackend` (formant fallback), and `TTSRouter` with 32-entry LRU cache.
  * **Primary-School Text Adaptation**: Oral fraction conversions, LaTeX sanitization, exponent reading, and natural sentence pacing (`core/tts/text.py`).
  * **Mayan Language Routing Seam**: Dedicated routing seam for Mayan K'iche' (`quc_Latn`) in `TTSRouter` with fail-safe error isolation (`503 Service Unavailable` when model checkpoint is absent).
  * **Latency & Acoustic Profiler**: CLI harness (`core/tts/profiler.py`, runnable via `uv run python -m core.tts.profiler`) measuring wall-clock synthesis time and Real-Time Factor ($0.237$s latency, $0.044$x RTF, exceeding $\le 3.0$s SLA by 92%).
  * **8GB Co-Resident Memory Budget**: Profile proving safe co-existence of local SLM (`llama.cpp` 4B Q4_K_M, ~2.80 GB) and neural TTS (~0.25 GB) inside 4.70 GB total working set (41.2% safety headroom).
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
   * Calibrated speech hyperparameters:
     * `length_scale = 1.12`: Slows delivery pace by 12% to facilitate comprehension for elementary students.
     * `noise_scale = 0.35`: Eliminates wobbly pitch artifacts, robotic warble, and acoustic peaking.
     * `noise_w_scale = 0.45`: Enforces steady, intelligible syllable cadence.
3. **Pluggable Voice Router & Neural Piper Engine (`backend/src/core/tts/`)**:
   * `protocols.py`: Formal `TTSBackend` protocol defining `synthesize()` and `is_available()`.
   * `piper.py`: High-fidelity neural synthesis using Piper VITS models on ONNX Runtime. Streams pure RIFF/WAV bytes in memory via `io.BytesIO` without disk I/O or temporary file locks.
   * **Automatic Config Sanitization**: Dynamically fixes legacy `"PhonemeType.ESPEAK"` string literals in `.onnx.json` model descriptors to prevent runtime enum exceptions.
   * `espeak.py`: Formant synthesizer implementing `TTSBackend` protocol as ultra-lightweight fallback.
   * `router.py`: Pluggable dispatcher selecting engines (`auto`, `piper`, `espeak`), routing Mayan K'iche' (`quc_Latn`) strictly to Piper, falling back gracefully from Piper to eSpeak for Spanish, and caching generated audio in an in-memory 32-entry LRU cache.
   * `api/session/speech.py`: Refactored to delegate synthesis directly to `core.tts.synthesize_speech()`.
4. **Latency Profiler & Benchmark Harness (`backend/src/core/tts/profiler.py`)**:
   * Diagnostic profiler measuring wall-clock synthesis time, audio duration, Real-Time Factor (RTF), sample rate, and peak amplitude levels.
   * Executable directly from terminal via `uv run python -m core.tts.profiler` or programmatically via `profile_speech_synthesis()`.
   * Empirical results: **0.237 s latency**, **0.044x RTF** (22.8x faster than real-time playback), meeting the $\le 3.0$s SLA requirement with a 92% margin.
5. **Jetson Orin Nano 8GB Unified Memory Profile**:
   * Detailed RAM budget co-locating `llama.cpp` (4B model, ~2.80 GB RSS), Piper-TTS VITS (~0.25 GB RSS), FastAPI (~0.15 GB), SQLite WAL (~0.50 GB), and OS (~1.00 GB).
   * Total active working set: **~4.70 GB (58.8%)**, maintaining **3.30 GB (41.2%)** in safety headroom.
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
   * Explain why **Piper-TTS VITS** on ONNX Runtime was chosen: human-sounding natural enunciation, sub-second latency ($0.237$s), ~150MB RAM footprint, and architectural routing support for Mayan language checkpoints (`quc_Latn`).
   * Why Spanish Harvard Sentences (`es_ES-sharvard-medium`, Speaker 1) was selected as the educational default over Mexican regional voices (`es_MX-ald`, `es_MX-claude`): neutral, textbook-clean diction preventing regional bias in Central American classrooms.
2. **Deterministic >51% Gating (Targeted Intervention vs Narration)**:
   * Emphasize that TutorBox is **not a screen reader**: voice feedback is a targeted pedagogical intervention triggered strictly when $>51\%$ of the class share the exact same conceptual misconception:
     $$\frac{\text{distractor\_votes}}{\text{total\_votes}} > 0.51$$
   * Ties, dispersed wrong answers, majority correct, or exact 51.0% remain strictly silent to avoid classroom audio fatigue.
3. **Hardware Budget & Memory Co-Existence**:
   * Present the Jetson Orin Nano 8GB memory budget: co-existing comfortably with `llama.cpp` (4B model) inside 4.70 GB total RAM (41.2% safety margin).
4. **End-to-End Live Proof**:
   * Reference the 10-round classroom match simulation (`test_session_10_round_speech.py`) demonstrating consistent, deterministic gating across all 10 pedagogical scenarios.
