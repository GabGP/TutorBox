# Offline Spanish TTS Engine A/B Benchmarking

This directory contains the benchmarking harness, fixed mathematical intervention corpus, and evaluation tooling for offline classroom speech synthesis on the TutorBox edge appliance (NVIDIA Jetson Orin Nano).

---

## 1. Quick Start

Run all commands from the repository root:

```bash
# 1. Single-run diagnostic profiler (latency, RTF, sample rate, peak amplitude):
python tools/benchmark/tts/metrics.py --engine qwen3-tts

# 2. Multi-engine A/B comparative sweep (cold start + warm repetitions):
python tools/benchmark/tts/ab.py --engines qwen3-tts,sherpa,piper,espeak --repeats 3 --out tools/benchmark/tts/results/

# 3. Full comparative sweep across the candidate engines and complete math corpus:
python tools/benchmark/tts/ab.py --engines qwen3-tts,sherpa,piper,kokoro,melo --repeats 5 --all-texts --out tools/benchmark/tts/results/
```

> **Note**: TutorBox uses `uv` for dependency management (`uv run python ...`); invoking `python` directly is also supported in the active development environment.

The integrated `qwen3-tts` backend is the benchmark entry point. `harness_melo.py` remains as a standalone reference for the rejected MeloTTS spike. There is no separate Qwen harness.

---

## 2. Benchmark Artifacts & Output Structure

All generated audio files, timing summaries, and profiling data are written to `tools/benchmark/tts/results/` (strictly gitignored via `.gitignore`):

```text
tools/benchmark/tts/results/
  out/
    qwen3-tts_es_0.wav   # Blind audio output for jury evaluation
    sherpa_es_0.wav
    piper_es_0.wav
    espeak_es_0.wav
  summary.csv            # Comprehensive tabular metrics across evaluated runs
```

### Metrics Schema in `summary.csv`

| Field | Unit | Description |
| :--- | :--- | :--- |
| `engine` | string | Canonical speech-engine identifier (`qwen3-tts`, `sherpa`, `piper`, `espeak`, etc.) |
| `provider` | string | Resolved execution class (`cuda` or `cpu`); Qwen is detected from `llama-tts --list-devices` |
| `cold_first_s` | seconds | Wall-clock latency of the first unprimed synthesis invocation |
| `warm_p50_s` | seconds | Median latency across subsequent repetitions |
| `warm_p95_s` | seconds | 95th percentile warm latency |
| `rtf_p50` | ratio | Median Real-Time Factor (`latency / audio_duration`) |
| `peak` | normalized | Peak absolute PCM amplitude; production engines target `0.78` |
| `sr_hz` | Hertz | Native output sample rate from the selected model/runtime |
| `wav_kb` | KB | Uncompressed RIFF/WAVE file size |
| `load_ms` | ms | Model loading / runtime warm-up duration |
| `rss_delta_mb` | MB | Peak Host RAM resident memory growth across process tree |
| `vram_delta_mb` | MB | Peak GPU Device VRAM allocation (CUDA) |
| `rss_scope` | string | Memory topology (`uma-unified` on Jetson, `discrete-vram`, or `host-only`) |

### Latest local comparison

The current first-corpus CSV shows Qwen3-TTS on CUDA at `2.290 s` warm p50 and `0.2386x` RTF (4.19x realtime) with `2,976 MB` peak host RAM and `3,272 MB` peak VRAM, passing the `<= 3.0s` classroom SLA. Sherpa-ONNX is `0.388 s` / `0.0474x` (+192 MB host RAM), Piper is `0.405 s` / `0.0495x` (+202 MB host RAM), Kokoro is `2.315 s` / `0.2781x` (+488 MB host RAM), and eSpeak is `0.325 s` / `0.0306x` (+9.6 MB host RAM). Qwen is the quality winner; Sherpa and Piper are the speed-oriented fallbacks.

---

## 3. Peak Level & Sample Rate Interpretation

Peak amplitude is not a loudness or quality score. The earlier CSV mixed native levels (`espeak` and Piper near `1.0`, Melo at `0.611`) with engines that already normalized to `0.78` (Sherpa/Kokoro/Qwen). Production Piper, eSpeak, and Qwen outputs now pass through the same linear PCM peak calibration, so new comparisons are apples-to-apples at `0.78` without digital clipping.

Sample rates differ because each model emits its native PCM rate: Piper/Sherpa use the Spanish VITS checkpoint at `22,050 Hz`, Qwen3-TTS emits `24,000 Hz`, Kokoro emits `24,000 Hz`, Melo's reference harness emits `44,100 Hz`, and eSpeak commonly emits `22,050 Hz`. The `12 Hz` in Qwen3-TTS refers to its codec/token frame rate, not the WAV sample rate. Resampling is unnecessary for normal browser playback; add one explicit output resampler only if a hardware codec requires a single fixed rate.

---

## 4. SLA & Quality Gates

Every candidate engine must pass both the quantitative and qualitative gates:

1. **SLA Response Gate**:
   - **Warm Latency**: `<= 3.0` seconds (required for timely classroom intervention).
   - **Cold Start**: `< 15.0` seconds (must be absorbable during the 20s student voting period).
   - **RTF**: `< 0.50x` (synthesis completes well before speech finishes playing).
2. **Acoustic Gate**:
   - **Peak Level**: `0.70 <= peak <= 0.85` after production calibration.
   - **Licensing**: Permissive open source (Apache 2.0 or MIT) suitable for offline deployment.
3. **Pedagogical Gate**:
   - Standard Spanish diction (clear pronunciation of mathematical terms: *denominador, simplificación, tres cuartos, cien por ciento*).
   - Calm, measured cadence appropriate for primary-school students.

---

## 5. Intervention Corpus (`corpus/es_math.txt`)

The corpus contains representative pedagogical intervention explanations generated during >51% distractor rounds. It is frozen during comparative evaluation rounds so every engine receives identical input text.

---

## 6. Candidate Engine Specifications

Detailed architectural profiles and spike notes for each engine reside in the `engines/` directory:

- [Qwen3-TTS (Primary Winner)](engines/qwen3-tts.md)
- [Sherpa-ONNX (Secondary)](engines/sherpa.md)
- [Piper (Tertiary Baseline)](engines/piper.md)
- [eSpeak (Ultimate Fallback)](engines/espeak.md)
- [Moss-Nano](engines/moss-nano.md)
- [Kokoro-ES](engines/kokoro.md)
- [MeloTTS reference](engines/melo.md)
