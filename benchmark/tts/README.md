# Offline Spanish TTS Engine A/B Benchmarking

This directory contains the benchmarking harness, fixed mathematical intervention corpus, and evaluation tooling for offline classroom speech synthesis on the TutorBox edge appliance (NVIDIA Jetson Orin Nano).

---

## 1. Quick Start

Run all commands from the repository root:

```bash
# 1. Single-run diagnostic profiler (prints latency, RTF, sample rate, peak amplitude):
python benchmark/tts/metrics.py --engine piper

# 2. Multi-engine A/B comparative sweep (measures cold start + warm repetitions):
python benchmark/tts/ab.py --engines piper,espeak --repeats 3 --out benchmark/tts/results/

# 3. Full comparative sweep across all candidates against the complete math corpus:
python benchmark/tts/ab.py --engines piper,sherpa,moss-nano,kokoro,melo,qwen-gguf --repeats 5 --all-texts --out benchmark/tts/results/
```

> **Note**: While TutorBox uses `uv` for dependency management (`uv run python ...`), in the active development environment invoking `python` directly is fully supported.

---

## 2. Benchmark Artifacts & Output Structure

All generated audio files, timing summaries, and profiling data are written to `benchmark/tts/results/` (strictly gitignored via `.gitignore`):

```text
benchmark/tts/results/
  out/
    piper_es_0.wav          # Blind audio output for jury evaluation
    espeak_es_0.wav
    sherpa_es_0.wav
  summary.csv               # Comprehensive tabular metrics across all evaluated runs
```

### Metrics Schema in `summary.csv`

| Field | Unit | Description |
| :--- | :--- | :--- |
| `engine` | string | Identifier of the speech engine (`piper`, `espeak`, `sherpa`, etc.) |
| `cold_first_s` | seconds | Wall-clock latency of the first unprimed synthesis invocation |
| `warm_p50_s` | seconds | Median latency across subsequent warm repetitions |
| `warm_p95_s` | seconds | 95th percentile warm latency (worst-case jitter under load) |
| `rtf_p50` | ratio | Median Real-Time Factor ($\text{latency} / \text{audio\_duration}$) |
| `peak` | normalized | Peak absolute amplitude ($0.0 \dots 1.0$), targeted at $0.70 \dots 0.85$ |
| `sr_hz` | Hertz | Output audio sample rate (e.g. 22050 Hz or 48000 Hz) |
| `wav_kb` | KB | Uncompressed RIFF/WAVE file size |
| `load_ms` | ms | Model weight loading / warm-up duration |
| `rss_delta_mb`| MB | Resident memory growth after initialization |

---

## 3. SLA & Quality Gates

Every candidate engine must pass both the quantitative and qualitative gates:

1. **SLA Response Gate**:
   - **Warm Latency**: $\le 3.0$ seconds (required for timely classroom intervention).
   - **Cold Start**: $< 15.0$ seconds (must be absorbable during the 20s student voting period).
   - **RTF**: $< 0.50\times$ (synthesis completes well before speech finishes playing).
2. **Acoustic Gate**:
   - **Peak Level**: $0.70 \le \text{peak} \le 0.85$ (no digital clipping, loud enough for 15-student classroom audio).
   - **Licensing**: Permissive open source (Apache 2.0 or MIT) suitable for offline deployment.
3. **Pedagogical Gate**:
   - Standard Spanish diction (clear pronunciation of mathematical terms: *denominador, simplificación, tres cuartos, cien por ciento*).
   - Calm, measured cadence appropriate for primary school students.

---

## 4. Intervention Corpus (`corpus/es_math.txt`)

The corpus contains representative pedagogical intervention explanations generated during >51% distractor rounds. It is frozen during comparative evaluation rounds to ensure identical input text across all engines.

---

## 5. Candidate Engine Specifications

Detailed architectural profiles and spike notes for each engine reside in the `engines/` directory:
- [Piper (Baseline)](engines/piper.md)
- [Sherpa-ONNX](engines/sherpa.md)
- [Moss-Nano](engines/moss-nano.md)
- [Kokoro-ES](engines/kokoro.md)
- [MeloTTS](engines/melo.md)
- [Qwen-GGUF](engines/qwen-gguf.md)
