# Architecture Reference: Offline Voice Feedback & Neural TTS Pipeline

## 1. Overview & Pedagogical Purpose

TutorBox applies the deterministic **>51% Rule** before any speech is generated:

$$\frac{\text{distractor\_votes}}{\text{total\_votes}} > 0.51$$

When one diagnostic distractor exceeds 51% of submitted student votes, the edge appliance speaks the conceptual explanation to the classroom. If the class splits its votes, selects the correct answer, or reaches a tie, the appliance remains silent.

The Spanish engine order is quality-first, with explicit speed and availability fallbacks:

```text
Qwen3-TTS  ->  Sherpa-ONNX  ->  Piper  ->  eSpeak-ng
 primary        secondary       tertiary    ultimate fallback
```

## 2. Acoustic Engine Comparison: Multi-Tier Hierarchy

| Dimension | Primary Neural Winner (`Qwen3-TTS`) | Secondary (`Sherpa-ONNX`) | Tertiary (`Piper`) | Ultimate Fallback (`eSpeak-ng`) |
| :--- | :--- | :--- | :--- | :--- |
| **Synthesis Technique** | 1.7B autoregressive model + 12 Hz codec/vocoder | VITS on Sherpa-ONNX | VITS on Piper | Rule-based formant synthesis |
| **Acoustic Fidelity** | Highest naturalness and prosody observed | Clear, natural educational diction | Clear, fast educational diction | Robotic and metallic, but dependable |
| **Hardware Target** | CUDA GPU via `llama-tts -ngl 99` | ONNX Runtime CPU/CUDA | Python VITS runtime | CPU only |
| **Synthesis Latency** | **2.090 s** warm p50 | **0.338 s** warm p50 | **0.274 s** warm p50 | **0.215 s** warm p50 |
| **RTF** | **0.2397x** | **0.0413x** | **0.0334x** | **0.0203x** |
| **Output Sample Rate** | 24,000 Hz | 22,050 Hz | 22,050 Hz | Commonly 22,050 Hz |
| **Production Peak** | 0.78 | 0.78 | 0.78 | 0.78 |
| **Mayan Support** | Not used for K'iche' routing | Spanish candidate only | Dedicated `quc` model slot | Only if an installed voice exists |
| **System Role** | **Primary winner (`qwen3-tts`)** | **Secondary neural fallback** | **Tertiary neural fallback** | **Ultimate safety net** |

Kokoro remains an experimental opt-in candidate. MeloTTS remains a rejected reference spike, with `harness_melo.py` intentionally retained for comparison.

## 3. Qwen3-TTS Model, CUDA, and Voices

TutorBox uses the **Qwen3-TTS 1.7B Base** model in GGUF format through `llama-tts`. The canonical engine identifier is `qwen3-tts`; `qwen-gguf` and `qwen` remain compatibility aliases only.

The local workstation's `llama-tts --list-devices` reports an NVIDIA CUDA device, and verbose synthesis logs report `using device CUDA0`. The CSV's Qwen result is therefore GPU-backed. Qwen is still slower than Sherpa/Piper because it generates codec tokens autoregressively, runs a neural vocoder, and currently uses a one-shot CLI process for each uncached request.

The deployed **Base** checkpoint has no fixed named-speaker catalog. TutorBox exposes it as `base-default`; Base is intended for reference-audio voice cloning, but the current backend does not yet wire a reference audio file into the API. Qwen's separate **CustomVoice** checkpoints provide `Vivian`, `Serena`, `Uncle_Fu`, `Dylan`, `Eric`, `Ryan`, `Aiden`, `Ono_Anna`, and `Sohee`. Those speakers are not selectable in the current Base deployment. See the [official Qwen3-TTS speaker documentation](https://github.com/QwenLM/Qwen3-TTS#custom-voice-generate).

## 4. Spanish Model Selection & Dialect Analysis

The selected Spanish neural checkpoint is `es_ES-sharvard-medium`, shared by the Sherpa-ONNX and Piper fallback tiers. It provides neutral, textbook-clean diction for Central American classrooms. Qwen3-TTS is preferred for natural prosody and mathematical sentence handling; Sherpa/Piper are preferred when response time or memory pressure dominates.

## 5. Mayan Language Routing Seam: K'iche' (`quc_Latn`)

Formant synthesis does not provide a dependable K'iche' phonological inventory. The voice subsystem therefore keeps a separate routing seam:

* **Language Identifier**: `quc` / `quc_Latn` (Mayan K'iche' in Latin orthography).
* **Router Isolation**: `lang=quc` dispatches to the configured Piper K'iche' checkpoint (`TTS_PIPER_MODEL_QUC`).
* **Strict Error Gating**: If the K'iche' checkpoint is absent, the system returns `503 Service Unavailable` rather than silently speaking Spanish.
* **eSpeak Exception**: eSpeak is used for K'iche' only when `TTS_VOICE_QUC` names an installed compatible voice.

Qwen3-TTS is not part of the K'iche' auto path because the deployed voice and validation assets are Spanish-first.

## 6. Peak Calibration & Sample-Rate Policy

`peak` in `summary.csv` is the largest absolute PCM sample divided by 32,768. It is not perceived loudness. Earlier results mixed native levels: eSpeak and Piper reached `1.00`, Melo measured `0.611`, while Sherpa/Kokoro normalized to `0.78` and Qwen was calibrated to `0.78`. Production Piper, eSpeak, and Qwen now share the same linear peak calibration target (`0.78`), so new CSV comparisons are consistent without clipping.

Each engine preserves the sample rate declared by its model/runtime:

| Engine | Native rate | Reason |
| :--- | ---: | :--- |
| Qwen3-TTS | 24,000 Hz | Qwen neural codec/vocoder output |
| Sherpa-ONNX | 22,050 Hz | Spanish Piper-compatible VITS checkpoint |
| Piper | 22,050 Hz | Spanish VITS checkpoint |
| Kokoro | 24,000 Hz | Kokoro model output |
| Melo reference harness | 44,100 Hz | Melo model/reference implementation |
| eSpeak-ng | Commonly 22,050 Hz | CLI voice/runtime default |

The Qwen `12 Hz` label is its codec/token frame rate, not its WAV sample rate. Browser playback accepts these PCM rates; resampling belongs at a hardware-output boundary only if a codec requires one fixed rate.

## 7. Empirical Latency & Real-Time Factor Benchmarks

The current first-corpus `summary.csv` reports:

| Engine | Provider | Warm p50 | RTF | Peak | Sample rate |
| :--- | :--- | ---: | ---: | ---: | ---: |
| Qwen3-TTS | CUDA | 2.090 s | 0.2397x | 0.78 | 24,000 Hz |
| Sherpa-ONNX | CPU | 0.338 s | 0.0413x | 0.78 | 22,050 Hz |
| Piper | CPU | 0.274 s | 0.0334x | 0.78 after recalibration | 22,050 Hz |
| eSpeak-ng | CPU | 0.215 s | 0.0203x | 0.78 after recalibration | 22,050 Hz |

Use the integrated profiler for new measurements:

```bash
uv run python benchmark/tts/metrics.py --engine qwen3-tts
uv run python benchmark/tts/ab.py --engines qwen3-tts,sherpa,piper,espeak --repeats 3
```

## 8. Configuration & Appliance Memory Policy

The relevant `.env` settings are `TTS_ENGINE=auto`, `TTS_QWEN_BINARY`, `TTS_QWEN_GGUF_PATH`, `TTS_QWEN_THREADS`, `TTS_SHERPA_PROVIDER`, `TTS_SHERPA_THREADS`, `TTS_PIPER_MODEL_DIR`, and `TTS_ESPEAK_BINARY`.

`TTS_QWEN_BINARY` is optional. Empty configuration searches next to the selected model, standard Windows/Linux install locations, and `PATH`; TutorBox deliberately does not scan the entire computer recursively. A normal `llama-tts` installation works when it adds the executable to `PATH`; set the variable for a non-standard location.

Question generation and speech playback are lifecycle-separated. The application can unload the local SLM before loading Qwen3-TTS, avoiding GPU/unified-memory contention. Sherpa/Piper are the preferred low-footprint choices when Qwen cannot be resident.

## 9. Phased Lifecycle Management Endpoints

The backend exposes quiz-agnostic lifecycle endpoints:

### TTS Lifecycle (`/api/v1/tts/*`, Teacher/Admin)

* `POST /api/v1/tts/load`: `{engine?, lang?, voice?}` -> `202 Accepted {engine, loaded, model_id, load_ms}`.
* `POST /api/v1/tts/unload`: `{engine?}` -> `200 OK {engine, loaded: false}`.
* `GET /api/v1/tts/status`: `{engine?, lang?}` -> `200 OK {engine, loaded, model_id}`.
* `GET /api/v1/tts/voices`: `?lang=es|quc` -> configured voice/model identifiers. Qwen currently returns `base-default`.

### LLM Lifecycle Proxy (`/api/v1/llm/*`, Admin Only)

* `POST /api/v1/llm/load`: Proxies model load to the local `llama-server`.
* `POST /api/v1/llm/unload`: Proxies model unload to the local `llama-server`.
* `GET /api/v1/llm/status`: Proxies model residency query to the local `llama-server`.
