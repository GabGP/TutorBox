# Architecture Reference: Offline Voice Feedback & Neural TTS Pipeline

## 1. Overview & Pedagogical Purpose

In TutorBox, voice feedback operates under the **Deterministic >51% Rule**:
$$\frac{\text{distractor\_votes}}{\text{total\_votes}} > 0.51$$

When a single diagnostic distractor exceeds 51% of submitted student votes in a classroom quiz round, the edge appliance speaks the conceptual explanation out loud to the classroom. If the class split their votes, selected the correct answer, or reached a tie, the appliance remains strictly silent.

This document details the offline acoustic pipeline, engine trade-offs, model selection criteria, latency benchmarks, hyperparameter calibration, and memory budget on the NVIDIA Jetson Orin Nano (8GB unified memory).

---

## 2. Acoustic Engine Comparison: Formant vs Neural

| Dimension | Formant Synthesis (`espeak-ng`) | Neural Synthesis (`Piper-TTS` VITS) |
| :--- | :--- | :--- |
| **Synthesis Technique** | Rule-based formant filter modeling | Variational Inference Text-to-Speech (VITS) on ONNX Runtime |
| **Acoustic Fidelity** | Robotic, metallic timbre | Natural, human-sounding pedagogical enunciation |
| **Model Footprint** | 0 MB (procedural algorithms) | ~60–80 MB per language checkpoint |
| **Runtime Memory (RSS)** | ~10 MB peak (ephemeral process) | ~150–250 MB in RAM (co-resident with `llama.cpp`) |
| **Synthesis Latency** | ~0.08 s (RTF ~0.015x) | **0.237 s** (RTF **0.044x** in-memory streaming) |
| **Mayan Language Support** | None (no Mayan phoneme inventory) | Extensible routing slot (`lang=quc`) with fail-safe error isolation |
| **System Role in TutorBox** | Zero-dependency safety fallback | **Primary classroom voice engine** |

---

## 3. Spanish Model Selection & Dialect Analysis

During Week 4 development, multiple Spanish ONNX acoustic checkpoints were evaluated for primary-school educational clarity:

1. **`es_MX-ald-medium` & `es_MX-claude-high`**:
   - *Observation*: Strong Mexican regional cadence, exaggerated pitch contours, and occasional harsh vocal peaking on unvoiced stops.
   - *Jury Conclusion*: Unsuitable as the primary textbook voice across diverse Central American classrooms.
2. **`es_ES-davefx-medium`**:
   - *Observation*: Clear male enunciation, but exhibited clipping and micro-distortion on high-volume classroom audio transducers.
3. **`es_ES-sharvard-medium` (Spanish Harvard Sentences - SELECTED)**:
   - *Acoustic Quality*: Trained on balanced phonetically rich Harvard sentences. Neutral, textbook-clean diction without distracting regional slang or exaggerated intonation.
   - *Multi-Speaker Architecture*:
     - **Speaker 1 (Default)**: Neutral female classroom educator.
     - **Speaker 0**: Neutral male classroom educator.

---

## 4. Mayan Language Routing Seam: K'iche' (`quc_Latn`)

Formant synthesizers (`espeak-ng`) lack phonological rules and triphone inventories for Mayan languages. The TutorBox voice subsystem establishes a formal architectural seam for Mayan languages:

* **Language Identifier**: `quc` / `quc_Latn` (Mayan K'iche' in Latin orthography).
* **Router Isolation**: Requesting `GET /api/v1/session/{id}/speech?lang=quc` dynamically dispatches to the configured Mayan voice model (`TTS_PIPER_MODEL_QUC`, default `quc_Latn-maya-medium.onnx`).
* **Strict Error Gating**: If the designated K'iche' checkpoint is not present on disk, the system explicitly returns `HTTP 503 Service Unavailable` with a descriptive message rather than silently falling back to Spanish audio.
* **Roadmap & Acoustic Feasibility**: Piper-TTS uses the VITS architecture, which can be fine-tuned on custom datasets with phonetic alphabets. Research projects like Meta MMS (Massively Multilingual Speech) offer raw acoustic checkpoints and text corpora for K'iche', but converting, pruning, and validating an ONNX model for real-time Piper inference remains a future milestone deliverable rather than a tested Week 4 artifact. All verified neural synthesis in Week 4 utilizes the Spanish Harvard Sentences checkpoint.

---

## 5. Hyperparameter Calibration for Classroom Intelligibility

Raw neural speech can sound rushed or prone to pitch wobble. TutorBox fine-tunes three acoustic parameters via `SynthesisConfig`:

* **`length_scale = 1.12` (Pedagogical Cadence)**:
  - Slows speech delivery by ~12% relative to conversational pace.
  - Ensures primary school students can parse mathematical terms (e.g. fractions and negative numbers).
* **`noise_scale = 0.35` (Acoustic Generator Stability)**:
  - Constrains the variance of the stochastic duration generator.
  - Eliminates robotic warbling, wobbly pitch artifacts, and audio peaking.
* **`noise_w_scale = 0.45` (Syllable Timing Regularity)**:
  - Calibrates phoneme duration predictability, maintaining crisp syllable separation.

---

## 6. Empirical Latency & Real-Time Factor (RTF) Benchmarks

All tests executed with `es_ES-sharvard-medium.onnx` on ARM64 / x86_64 architecture:

* **Sample Text**: *"Atención: 100 por ciento del grupo respondió un medio. Dividiste sólo el numerador entre 2. La respuesta correcta es tres cuartos."*
* **Audio Length**: $5.41$ seconds of 22,050 Hz PCM audio.
* **Wall-Clock Latency**: **0.237 seconds**.
* **Real-Time Factor (RTF)**: **0.044x** (synthesis runs **22.8 times faster than real-time playback**).
* **Target SLA**: $\le 3.0$ seconds (empirically achieved with **92.1% safety margin**).
* **Peak Audio Level**: $0.78$ normalized (preventing clipping on classroom speakers).

### Profiler Usage & Verification Guide

The offline synthesis profiler (`core.tts.profiler`) measures wall-clock latency, audio duration, Real-Time Factor (RTF), sample rate, and peak amplitude on the target appliance.

#### 1. Running the CLI Benchmark
To benchmark the active speech synthesis pipeline from the command line:
```bash
# From the backend directory:
uv run python -m core.tts.profiler
# or directly:
python -m core.tts.profiler
```

Example terminal output:
```text
Benchmarking TutorBox Neural TTS Pipeline...
Latency:      0.237 s
Audio Length: 5.41 s
RTF:          0.044x
Sample Rate:  22050 Hz
Peak Level:   0.78 (normalized)
WAV Size:     233.2 KB
```

#### 2. Programmatic Python API
The profiler can be called programmatically to inspect latency or validate SLA constraints:
```python
from core.tts.profiler import ProfileResult, profile_speech_synthesis

# Run synthesis benchmark (bypasses cache for accurate timing)
result: ProfileResult = profile_speech_synthesis(
    text="Atención: el 60 por ciento respondió un medio.",
    lang="es",  # or "quc"
    voice=None,  # custom voice checkpoint name if needed
)

print(f"Latency:   {result.latency_seconds:.3f} s")
print(f"Duration:  {result.audio_duration_seconds:.2f} s")
print(f"RTF:       {result.real_time_factor:.3f}x")
print(f"Peak Level:{result.peak_amplitude:.2f}")

# Assert SLA compliance (<= 3.0s ceiling)
assert result.latency_seconds <= 3.0, "TTS latency violated SLA ceiling"
```

#### 3. Metrics Reference
* `latency_seconds`: Wall-clock synthesis elapsed time from request to complete WAV bytes.
* `audio_duration_seconds`: Total playback time of the generated WAV audio.
* `real_time_factor` (RTF): `latency_seconds / audio_duration_seconds`. Values below $1.0\times$ mean faster than real-time playback (e.g. $0.044\times$ = 22.8x faster).
* `sample_rate`: PCM sampling frequency in Hz (typically 22,050 Hz for Piper medium models).
* `peak_amplitude`: Peak absolute sample divided by 32,768 ($0.0 \dots 1.0$). Levels around $0.70 \dots 0.85$ prevent speaker distortion and clipping.
* `audio_byte_count`: Size of raw RIFF/WAVE stream in bytes.

---

## 7. Multi-Voice Catalog Architecture (PWA Selection)

TutorBox provides a hardware-contained multi-voice design:
1. **Zero Online Downloads**: All authorized voice checkpoints are pre-installed in `.cache/models/tts/` or `/opt/tutorbox/models/tts/`.
2. **Configurable Environment Variables**:
   - `TTS_PIPER_MODEL_ES`: Switches between `sharvard-medium`, `davefx-medium`, or custom checkpoints.
   - `TTS_PIPER_SPEAKER_ES`: Toggles between female (`1`) and male (`0`) educators without reloading weights.
3. **Pluggable Router (`TTSRouter`)**: In-memory 32-entry LRU cache prevents redundant re-synthesis when multiple clients or replays request the same round audio.

---

## 8. Jetson Orin Nano 8GB Unified Memory Budget

The edge appliance runs headless Ubuntu Linux (JetPack 6.0) with unified memory shared between CPU and GPU:

```
+-------------------------------------------------------------+
|               8GB Unified Memory (Jetson Orin Nano)         |
+-------------------------------------------------------------+
| OS & Kernel Daemons:              1.00 GB (12.5%)           |
| Local SLM (llama.cpp 4B Q4_K_M):  2.80 GB (35.0%)           |
| Neural TTS (Piper-TTS VITS):      0.25 GB ( 3.1%)           |
| SQLite WAL & Buffer Cache:        0.50 GB ( 6.3%)           |
| FastAPI / Uvicorn Runtime:        0.15 GB ( 1.9%)           |
+-------------------------------------------------------------+
| Total Active Working Set:         4.70 GB (58.8%)           |
| RESERVED SAFETY HEADROOM:         3.30 GB (41.2%)           |
+-------------------------------------------------------------+
```

Even during concurrent 4B SLM quiz generation and Piper neural voice synthesis, memory utilization remains safely below 59%, leaving over 3.3 GB of RAM for OS page cache, HDMI display output, and transient loads.
