# Benchmarks (TTS Engines & SLM Generation)

Comparative evaluations, benchmarks, and acoustic listening tests live here — **not** in `backend/tests/` (which is reserved for deterministic unit/integration CI tests with a 300 LoC cap) and **not** in `backend/src/` (enforced by the 150 LoC ceiling in `test_modularity_policy.py`).

---

## 1. Directory Structure

```text
tools/benchmark/
  README.md                  # Comparative eval guide, hardware constraints & jury scorecard
  tts/
    README.md                # Quick start, SLA gates, and CLI usage
    ab.py                    # Multi-engine sweep runner -> CSV + blind WAVs
    metrics.py               # Profiler & acoustic metric analyzer
    corpus/
      es_math.txt            # Fixed Spanish pedagogical intervention corpus
    engines/
      piper.md               # Baseline: es_ES-sharvard-medium (spk 1, 22kHz VITS)
      sherpa.md              # Sherpa-ONNX runtime hosting Piper + Supertonic-3-es
      moss-nano.md           # Moss-Nano 100M ONNX CPU (native Spanish)
      kokoro.md              # Kokoro 82M (lang=e + espeak-ng G2P)
      melo.md                # MeloTTS Spanish (MIT lightweight VITS)
      qwen3-tts.md           # Qwen3-TTS 1.7B Base GGUF (primary neural voice)
    results/                 # GITIGNORED: generated WAVs, CSV logs, tegrastats
  llm/
    quiz_gen/                # Future: LLM prompt evaluation, rejection rates, SymPy passes
```

---

## 2. Hardware Constraints & Appliance Budget (NVIDIA Jetson Orin Nano 8GB)

TutorBox runs as a self-contained offline appliance with 8GB unified LPDDR5 memory shared between CPU and GPU.

| Subsystem | RAM / VRAM Budget | Target Real-Time SLA | Concurrency Model |
| :--- | :--- | :--- | :--- |
| **Linux OS + System Services** | ~1.5 GB | N/A | Background daemon |
| **FastAPI Backend + SQLite + Cache** | ~0.5 GB | < 50 ms API response | Single process, async worker |
| **Local SLM (`llama-server`)** | ~4.7 GB (Q4_K_M) | ~20–30 tokens/sec | Active during question gen / Socratic |
| **Offline Classroom TTS** | **0.25 – 0.50 GB** | **Warm latency <= 3.0 s** | Active at end of round (>51% rule) |
| **Free Safety Buffer** | ~1.0 GB | N/A | Prevents OOM kills |

### Memory Swapping vs. Co-Residency
- **Co-resident Path**: When total RAM <= 7.0 GB, SLM/LLM and TTS engine remain loaded in memory concurrently.
- **Phased Lifecycle Path**: When larger models are evaluated, the frontend/quiz manager triggers explicit lifecycle transitions:
  - Before generation: `POST /api/v1/llm/load` + `POST /api/v1/tts/unload`.
  - At round start: `POST /api/v1/llm/unload` + `POST /api/v1/tts/load` (the 20-second voting window easily absorbs the 1–3s unload + 1–2s preload).

---

## 3. Spanish TTS Candidate Engine Matrix

| Engine | Model / Architecture | License | Strengths | Fail Conditions | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Piper (Baseline)** | `es_ES-sharvard-medium` (VITS) | MIT | 0.237s warm latency, 0.044x RTF, 250MB RAM, clear educator voice | Fails if superseded in audio naturalness | **Active Baseline** |
| **eSpeak-NG** | Formant synthesis | GPLv3+ | 0.08s latency, 10MB RAM, zero neural weights | Robotic voice; fallback only | **Active Fallback** |
| **Sherpa-ONNX** | ONNX Runtime (Piper / Supertonic) | Apache 2.0 | Optimized C++ runtime, ARM NEON/Jetson wheels, multi-threaded | Warm > 3.0s or RSS delta > 500MB | Spike Candidate 1 |
| **Moss-Nano** | 100M ONNX CPU | Apache 2.0 | Torch-free ONNX, 48kHz output, native Spanish | Loss in jury score without latency gain | Spike Candidate 2 |
| **Kokoro-ES** | 82M StyleTTS2 variant | Apache 2.0 | High naturalness, compact size | Anglicized accent or G2P failures | Spike Candidate 3 |
| **MeloTTS** | Modular VITS | MIT | Native Spanish accents, fast CPU inference | Robotic cadence or licensing hurdles | Spike Candidate 4 |
| **Qwen3-TTS** | 1.7B Base GGUF | Apache 2.0 | Highest observed naturalness and prosody | One-shot CLI startup and unified-memory pressure | **Primary neural voice** |

---

## 4. Jury Listening Protocol & Scorecard

Benchmarking speech quality is not solely a numbers game; acoustic naturalness and pedagogical suitability are decisive.

### Evaluation Gates
1. **Deterministic Objective Gate**:
   - **Warm Latency**: $\le 3.0$ seconds (hard SLA).
   - **Cold First-Run**: $< 15.0$ seconds (accommodated by 20s question turn).
   - **Real-Time Factor (RTF)**: $< 0.50\times$ (synthesis faster than spoken duration).
   - **Normalized Peak Amplitude**: $0.70 \le \text{peak} \le 0.85$ (loud classroom projection without digital clipping).
   - **License**: Apache 2.0 or MIT (permissive, edge-distributable).
2. **Pedagogical Listening Gate (Blind Jury)**:
   - Evaluators listen to blind WAV samples (`results/out/<engine>_es_<idx>.wav`).
   - Criteria scored 1–5:
     - **Intelligibility**: Are mathematical terms (fractions, percentages, operations) crisp and distinct?
     - **Diction**: Neutral Latin American / standard Spanish pronunciation without heavy regional dialect or anglicisms.
     - **Pacing & Cadence**: Calm, measured teaching tempo suitable for primary school students (not rushed or disjointed).
     - **Artifacts**: Absence of robotic buzz, phoneme skipping, or synthetic clicking.

---

## 5. Execution Reference

```bash
# Run single-engine baseline check
python tools/benchmark/tts/metrics.py --engine piper

# Run comparative sweep across engines on the math corpus
python tools/benchmark/tts/ab.py --engines piper,espeak --repeats 3 --out tools/benchmark/tts/results
```
