# Utz'tutor — Offline Kʼicheʼ (`quc`) & Qʼeqchiʼ (`kek`) TTS Options & Plans for Jetson Orin Nano (8 GB)

Research & architectural design report for adding offline Mayan Text-to-Speech — **Kʼicheʼ** (ISO 639-3: `quc`) and **Qʼeqchiʼ** (ISO 639-3: `kek`) — to **Utz'tutor**, constrained strictly to models and pipelines that fit within the **NVIDIA Jetson Orin Nano (8 GB unified memory)** appliance budget.

> **Scope note:** No existing project files were modified; this document is the only output. All file paths, line numbers, memory numbers, and runtime constraints are grounded in the current repository state.

---

## 1. Executive Summary & Headline Recommendation

Utz'tutor already has a Kʼicheʼ (`quc`) routing seam and UI language selector, but **no actual Kʼicheʼ or Qʼeqchiʼ neural model is shipped or downloaded yet**, `kek` is not wired into the API or PWA, and every spoken explanation is currently generated in Spanish.

Every viable path below fits comfortably on the **8 GB Jetson Orin Nano**. The highest-leverage strategy is a **3-phase progression** rather than betting everything on one model:

1. **Ship both languages offline immediately (Co-resident, ~200 MB RAM):** Deploy **Meta MMS-TTS** (`facebook/mms-tts-quc-dialect_central` and `facebook/mms-tts-kek`) exported to ONNX inside Utz'tutor's existing **`sherpa-onnx`** runtime (**Option 1**), backed by a human-translated Kʼicheʼ/Qʼeqchiʼ bank for the **33 curriculum misconception slugs** and a Mayan-aware math/number normalizer. Enable the already-bundled `espeak-ng` `quc` voice as a zero-RAM fallback (**Option 7**).
2. **Upgrade classroom warmth & accuracy (0–200 MB RAM):** Record a local native Kʼicheʼ/Qʼeqchiʼ primary teacher for the **33 core misconceptions** (and optionally the 66 seed questions) as a **Tier-0 Pre-Recorded Audio Bank** (**Option 4**, 0 MB RAM, 10/10 authenticity), and use 15–45 minutes of those same recordings to **fine-tune MMS-TTS** (**Option 2**) for dynamically LLM-generated questions.
3. **Long-term 22–24 kHz / commercial-safe upgrade:** Train a clean-licensed **22.05 kHz Piper VITS** checkpoint in grapheme mode (`phoneme_type: "text"`) that drops straight into the existing `TTS_PIPER_MODEL_QUC` / `TTS_PIPER_MODEL_KEK` slot (**Option 3**, co-resident ~200 MB RAM), **or** fine-tune **`Qwen3-TTS-12Hz-0.6B-Base`** to GGUF for Utz'tutor's existing CUDA `llama-tts-daemon` (**Option 5**, phased ~1.6–1.9 GB RAM) once automatic SLM↔TTS lifecycle swapping is completed.

---

## 2. Current TutorBox Baseline & Codebase Findings

Inspecting the repository surfaced **seven concrete codebase facts** that directly shape any Mayan TTS plan:

1. **Kʼicheʼ seam exists, Qʼeqchiʼ does not:**
   - `quc` is wired in `backend/src/api/session/speech.py:32`, `backend/src/api/tts/schemas.py:26,64`, `backend/src/api/tts/endpoints.py:137-140`, `backend/src/core/tts/router/selection.py:43-66`, and `pwa/app/src/features/speech/VoicePicker.tsx:61-62`.
   - `kek` (Qʼeqchiʼ) is absent everywhere.
   - `DEFAULT_TTS_PIPER_MODEL_QUC = "quc_Latn-maya-medium.onnx"` (`backend/src/core/config/constants.py:50`) is a placeholder; `rhasspy/piper-voices` publishes **no** Kʼicheʼ or Qʼeqchiʼ ONNX checkpoints.
2. **Surprise discovery — `espeak-ng` already bundles Kʼicheʼ (`quc`) inside this repo's venv:**
   - `backend/src/core/config/constants.py:36` states `# no K'iche' voice ships with espeak-ng yet`, **but `piper-tts 1.8.0` in `.cache/venv` already ships**:
     - `.cache/venv/Lib/site-packages/piper/espeak-ng-data/lang/myn/quc` (`name K'iche'`, `language quc`, `status testing`, `stressRule 3 // stress on final syllable`)
     - `.cache/venv/Lib/site-packages/piper/espeak-ng-data/quc_dict`
   - `kek` (Qʼeqchiʼ) is **not** shipped in `espeak-ng-data`.
3. **`SherpaBackend` currently hard-requires eSpeak phonemes:**
   - `backend/src/core/tts/engines/sherpa/engine.py:111-114` unconditionally calls `phoneme_generation_config(...)` (which runs eSpeak-ng via `piper-tts` and passes `phoneme_codepoints`).
   - `backend/src/core/tts/engines/sherpa/metadata.py:53-56` unconditionally injects `"comment": "piper"` and `"has_espeak": "1"`.
   - Character-based VITS models like **Meta MMS-TTS** (`"comment": "mms"`, `"frontend": "characters"`) do **not** use eSpeak and must bypass `phoneme_codepoints`!
4. **`QwenBackend` silently drops 3-letter language codes (`quc`, `kek`) and hardcodes 1.7B filenames:**
   - `backend/src/core/tts/engines/qwen/engine.py:108`: `lang = voice if voice and len(voice) == 2 else "es"` resets `"quc"` and `"kek"` back to `"es"`.
   - `backend/src/core/tts/engines/qwen/models.py:90,96` hardcodes `Qwen3-TTS-12Hz-1.7B-Base-Q4_K_M.gguf` and `mmproj-Qwen3-TTS-12Hz-1.7B-Base-Q8_0.gguf`, blocking a 0.6B or language-specific GGUF without parameterization.
5. **The "Spanish Text Trap" — speech scripts and explanations are Spanish-only:**
   - `backend/src/modes/quiz/session/speech.py:34-38` hardcodes Spanish sentences:
     - `"Atención: {share} por ciento del grupo respondió {chosen_text}."`
     - `decision.explanation` (stored in Spanish in `quiz_questions.distractors_json`)
     - `"La respuesta correcta es {correct_text}."`
   - Feeding Spanish text into a Kʼicheʼ or Qʼeqchiʼ TTS model produces unintelligible garbled speech. Text localization is a hard prerequisite.
6. **The "Math & Digits Trap" in `normalize_for_speech()`:**
   - `backend/src/core/tts/text.py` rewrites fractions and operators into **Spanish** (`1/4` → `"un cuarto"`, `+` → `"más"`, `%` → `"por ciento"`).
   - **Critical for character-based models (MMS-TTS):** Meta's MMS `vocab.txt` files contain alphabetic characters and apostrophes, **not ASCII digits `0-9`**. Raw digits like `54` or `1/2` are dropped/unknown unless converted into spoken Kʼicheʼ or Qʼeqchiʼ words first.
   - Glottal stops (`ʼ` U+02BC vs `'` U+0027 vs `’` U+2019) are **phonemic** in both Kʼicheʼ and Qʼeqchiʼ (`bʼ, chʼ, kʼ, qʼ, tʼ, tzʼ`) and must be canonicalized to the exact character in each model's vocabulary — never stripped.
7. **Hard modularity ceilings are tight in TTS modules:**
   - `tests/test_modularity_policy.py` enforces **≤ 150 LoC** per file in `backend/src/` and **≤ 300 LoC** per test file, with **100% statement coverage** (`backend/pyproject.toml:51`).
   - Current line counts near the ceiling: `router/selection.py` (**150**), `router/router.py` (**149**), `api/tts/endpoints.py` (**144**), `core/config/tts_settings.py` (**143**), `engines/piper/engine.py` (**140**). Any additions here **must split out helper modules** rather than grow existing files.

---

## 3. Jetson Orin Nano (8 GB UMA) Memory Budget & Residency Rules

Per `docs/architecture/hardware-topology.md` and `docs/architecture/voice-feedback.md`, usable physical unified LPDDR5 RAM is **~7.5 GiB** shared by CPU and Ampere GPU.

| Subsystem | Footprint | Notes |
| :--- | :---: | :--- |
| Ubuntu 22.04 headless + kernel (25 W) | ~0.8 GB | Always resident |
| Firefox HDMI classroom kiosk | ~0.6 GB | Always resident |
| FastAPI + SQLite WAL + SymPy + Nginx | ~0.5 GB | Always resident |
| Dynamic classroom session pool (15–20 phones) | ~0.5 GB | Always resident |
| **Non-AI Fixed Baseline** | **~2.4 GB** | **~5.1 GB left for SLM + TTS + OS safety cache** |

This creates **two strict Jetson residency tiers**:

| Residency Regime | Available TTS RAM/VRAM | Operational Requirement |
| :--- | :---: | :--- |
| **Tier A: Co-Resident with SLM** | **≤ 500 MB** (ideal: ≤ 250 MB) | Works **today** with zero architectural changes. SLM stays loaded (`qwen2.5:3b` on Ollama ~2.5–3.2 GB or `Gemma 4 A2B Q4_K_M` ~4.7 GB) while TTS serves instant audio without OOM risk. |
| **Tier B: Phased Lifecycle (SLM Unloaded)** | **0.6 GB – 3.5 GB** | Requires implementing the automatic **SLM unload → TTS load** swap during the 20–30 s voting window (currently unbuilt per `docs/architecture/hardware-topology.md:85`, and `POST /api/v1/llm/unload` must support Ollama's `keep_alive: 0` in addition to `llama-server`). |

> **Important Jetson rule for `tools/voice_models`:** On Jetson Orin Nano, **avoid adding PyTorch (`torch`) as a runtime dependency** in `backend/pyproject.toml`. PyTorch on JetPack ARM64 adds ~600 MB–1.2 GB of RAM overhead and fragile CUDA wheel pinning. Prefer **`sherpa-onnx` / ONNX Runtime**, **`piper-tts`**, **`llama-tts-daemon` (GGUF/CUDA)**, **`espeak-ng`**, or **static audio files** — all of which are already part of Utz'tutor's stack.

---

## 4. Comparison Matrix: 7 Jetson-Viable Mayan TTS Options

| # | Option | Kʼicheʼ (`quc`) | Qʼeqchiʼ (`kek`) | Jetson RAM/VRAM | Disk / Lang | Est. Latency / RTF (Orin Nano) | Co-Resident w/ SLM? | Audio Quality | Audio Data Needed | License | Effort |
| :-: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | **Meta MMS-TTS → ONNX in `sherpa-onnx`** | Ready (3 dialects) | Ready (`kek`) | **~180–240 MB** (CPU) | ~145 MB FP32 (~40 MB INT8) | ~0.3–0.5 s (~0.05× RTF) | **Yes** (Tier A) | Fair–Good (16 kHz, formal Bible register) | **0 hours** | **CC-BY-NC 4.0** (NonCommercial) | **Low** (days) |
| **2** | **Fine-Tuned MMS-TTS VITS → ONNX in `sherpa-onnx`** | Yes (fine-tune) | Yes (fine-tune) | **~180–240 MB** (CPU) | ~145 MB FP32 (~40 MB INT8) | ~0.3–0.5 s (~0.05× RTF) | **Yes** (Tier A) | Good–Very Good (16 kHz, warm local teacher) | **15–60 min** clean single-speaker | **CC-BY-NC 4.0** (inherits MMS) | **Medium** (1–2 wks) |
| **3** | **Custom Piper VITS (22.05 kHz, `piper1-gpl`)** | Yes (grapheme or `espeak quc`) | Yes (grapheme or custom `espeak kek`) | **~180–205 MB** (CPU) | ~65–76 MB | **~0.40 s** (~0.05× RTF) | **Yes** (Tier A) | Very Good (22.05 kHz, crisp educational voice) | **1–4 hours** clean single-speaker | **MIT / GPLv3 train, open weights** (commercial-safe!) | **Medium–High** (2–4 wks) |
| **4** | **Pre-Recorded Native Teacher Bank + Neural Fallback** | Yes (human) | Yes (human) | **~0 MB** | ~10 MB Opus / ~50 MB WAV | **< 20 ms** | **Yes** (Tier A) | **10/10** (authentic native teacher) | **33–200 short clips** (~10–90 min) | **Project-owned** (with speaker consent) | **Low–Medium** (1–2 wks) |
| **5** | **Fine-Tuned `Qwen3-TTS-0.6B` / `1.7B` GGUF (`llama-tts-daemon`)** | Yes (SFT) | Yes (SFT) | **~1.6–1.9 GB** (0.6B) / **~3.3–3.4 GB** (1.7B) | ~0.8 GB (0.6B) / ~1.5 GB (1.7B) | ~0.6–1.1× RTF (CUDA) | **No — Phased** (Tier B) | **Highest neural** (24 kHz, rich prosody, bilingual capable) | **1–5 hours** clean audio | **Apache 2.0** (Qwen3-TTS) | **High** (3–6 wks) |
| **6** | **Flow-Matching (`Matcha-TTS` in `sherpa-onnx` or `ZipVoice` TRT / `F5-TTS-ONNX`)** | Yes (train/FT) | Yes (train/FT) | **~220–350 MB** (Matcha) / **~0.8–2.2 GB** (ZipVoice/F5) | ~90 MB (Matcha) / ~350–700 MB (Zip/F5) | ~0.3–0.6 s (Matcha) / ~0.5–1.5 s (TRT) | Matcha: **Yes**; Zip/F5: **Phased** | Very Good (22–24 kHz; Zip/F5 clone teacher voice) | **1–10 hours** clean audio | **MIT / Apache 2.0** | **High** (3–5 wks) |
| **7** | **`eSpeak-ng` Formant (`quc` built-in + compiled `kek`)** | **Built-in now** (`status testing`) | Custom `kek_rules` compile | **~9–10 MB** (CPU) | < 1 MB | **~0.29 s** (~0.03× RTF) | **Yes** (Tier A) | Poor (robotic; weak ejectives/implosives) | **0 hours** (linguistic rules for `kek`) | **GPLv3** | **Trivial (`quc`) / Low (`kek`)** |

---

## 5. Shared Cross-Cutting Prerequisites (Required for All Options)

Before (or alongside) plugging in any engine from Section 6, five shared seams in Utz'tutor must be extended so Kʼicheʼ and Qʼeqchiʼ work cleanly end-to-end.

### 5.1 Expand Language Contracts from `es | quc` to `es | quc | kek`
- **Backend API & schemas:**
  - `backend/src/api/session/speech.py:32` → `SpeechLanguage = Literal["es", "quc", "kek"]`
  - `backend/src/api/tts/schemas.py:26,64` → `Literal["es", "quc", "kek"]`
  - `backend/src/api/tts/preview.py:18-21` → add native-verified primary-school preview strings for `"quc"` (replacing placeholder `"Utz'tutor."`) and `"kek"`.
  - `backend/src/api/tts/endpoints.py:107-144` → extract voice-listing builders into a new helper module `api/tts/voice_catalog.py` (keeps `endpoints.py` ≤ 150 LoC) and handle `lang in ("quc", "kek")`.
- **Router isolation (preserve strict 503 gating):**
  - Split `backend/src/core/tts/router/selection.py` (currently at **150/150 LoC**) by extracting Mayan routing into `core/tts/router/mayan_selection.py`.
  - Generalize `_resolve_quc_backend` into `_resolve_mayan_backend(lang: Literal["quc", "kek"], ...)` so neither `quc` nor `kek` can ever silently fall back to Spanish audio (returns `503 Service Unavailable` when unconfigured).
- **Config & PWA:**
  - Split Mayan TTS config fields into `core/config/mayan_tts_settings.py` (since `tts_settings.py` is 143 LoC) and document all `TTS_*_QUC` / `TTS_*_KEK` vars in `.env.example`.
  - Update `pwa/app/src/features/speech/speech.types.ts:1` (`'es' | 'quc' | 'kek'`), `VoicePicker.tsx:61-62` (add `<option value="kek">Q&apos;eqchi&apos;</option>`), and `useVoicePicker.ts:30`.

### 5.2 Solve the "Spanish Text Trap" (Where Kʼicheʼ / Qʼeqchiʼ Text Comes From)
Utz'tutor's `CURRICULUM_TAXONOMY` (`backend/src/modes/quiz/contracts/taxonomy.py`) has **only 33 unique diagnostic misconception slugs** across all 4 topics and 10 subconcepts, plus **66 curated seed questions** (and 320 authored pool questions).

**Recommended 2-tier localization design (0 MB live RAM):**
1. **Curated Multilingual Misconception & Framing Bank (Primary — Zero Hallucination Risk):**
   - Localize `build_intervention_script()` (`backend/src/modes/quiz/session/speech.py`) with language-specific framing templates (`es`, `quc`, `kek`) reviewed by Guatemalan EBI (Educación Bilingüe Intercultural) teachers.
   - Add an idempotent SQLite migration (e.g., `backend/migrations/016_add_localized_explanations.sql`) storing:
     - `misconception_translations(slug, lang, explanation)` — human-authored Kʼicheʼ & Qʼeqchiʼ explanations for all **33 taxonomy slugs**.
     - `question_distractor_translations(question_id, option_key, lang, explanation)` — optional per-question overrides for the 66–386 curated questions and teacher-edited questions.
   - Resolution order when `GET /api/v1/session/{id}/speech?lang=quc|kek` runs:
     1. Exact `(question_id, dominant_distractor, lang)` translation if present.
     2. Fallback to `(decision.misconception, lang)` from the 33-slug table (covers **100% of dynamically LLM-generated questions** automatically with zero runtime translation model!).
     3. Return `503` if neither exists — never feed Spanish prose into a Mayan voice.
2. **Optional Offline MT Assist for Teacher Authoring (MADLAD-400-3B-MT INT8 on CTranslate2):**
   - **Important model-coverage fact:** Meta's **NLLB-200 does NOT natively support `quc` or `kek`**. Google's **`google/madlad400-3b-mt` DOES natively support both** (`<2quc>` and `<2kek>`).
   - Quantized to **INT8 in CTranslate2**, `madlad400-3b-mt` uses **~1.5–1.8 GB RAM** and can run offline on the Jetson (phased when SLM is unloaded) to draft a Kʼicheʼ/Qʼeqchiʼ translation when a teacher writes or generates a new question, saving it to SQLite for teacher review — **never** run blindly inside the live voting loop.

### 5.3 Mayan-Aware Text & Math Normalization (`core/tts/text.py` + `core/tts/text_mayan.py`)
Create `backend/src/core/tts/text_mayan.py` (keeping `text.py` under 150 LoC) and dispatch by `lang`:
1. **ALMG Glottal Stop Canonicalization:**
   - Map all apostrophe variants — U+02BC (`ʼ`), U+0027 (`'`), U+2019 (`’`), U+02C8 (`ˈ`), U+0060 (`` ` ``) — to the exact grapheme expected by the active model (verify against each checkpoint's `vocab.txt` / `tokens.txt`; e.g., Meta MMS checkpoints generally use ASCII `'` U+0027).
   - **Never strip apostrophes** inside `_MARKUP` or sanitizer regexes: `kaq` vs `kʼaq`, `chaj` vs `chʼaj`, `qul` vs `qʼul` are completely different words.
2. **Digit & Math Expression Expansion (Mandatory for MMS-TTS!):**
   - Character-based VITS models (`facebook/mms-tts-*`) **do not contain digits `0–9` in `vocab.txt`**. Passing `"67"` or `"3/4"` yields silence or garbled tokens.
   - Implement a deterministic number-to-words converter for `0..1000` (and common primary fractions/operators) in **Kʼicheʼ** (e.g., *jun, kebʼ, oxibʼ, kajibʼ, jobʼ…*) and **Qʼeqchiʼ** (e.g., *jun, wiibʼ, oxibʼ, kaahibʼ, oobʼ…*) — **or**, if local EBI teachers confirm students use Spanish loanwords for numbers > 20 and fractions, encode the agreed classroom convention explicitly in lookup tables.
3. **Unicode Normalization & OOV Filtering:**
   - Keep `unicodedata.normalize("NFC", text)`.
   - Strip markdown/LaTeX symbols, normalize whitespace, and filter characters not present in the target model's `tokens.txt` (logging a warning so missing glyphs are caught during testing).

### 5.4 Pre-Existing TTS Tech Debt to Fix Before Adding Mayan Engines
From `suggestions.md` (directly relevant to Jetson stability):
- **M5:** Add a `threading.Lock` around `TTSRouter.synthesize()` so concurrent preview/session calls never race.
- **M7:** Stop `SherpaBackend.is_available()` from calling `onnx.load()` on every request; move ONNX metadata generation strictly to download/build time (`tools/voice_models/`).
- **L7:** Pin Hugging Face revision SHAs and verify SHA-256 checksums in `tools/voice_models/catalog.py`.

---

## 6. Detailed Suggestions & Implementation Plans

---

### Option 1: Meta MMS-TTS (`vits-mms`) Exported to ONNX in Existing `sherpa-onnx`

**Verdict:** **Best Day-1 neural solution.** Immediately delivers offline neural speech for **both Kʼicheʼ and Qʼeqchiʼ** with **zero dataset collection, zero GPU training, zero new runtime dependencies**, and full co-residency with the SLM on the 8 GB Jetson Orin Nano.

#### Available Pre-Trained Checkpoints (Hugging Face)
- **Qʼeqchiʼ (`kek`):** `facebook/mms-tts-kek`
- **Kʼicheʼ (`quc`):**
  - `facebook/mms-tts-quc-dialect_central` *(recommended default — broadest intelligibility across Totonicapán, Quetzaltenango, Santa Cruz del Quiché, Sololá)*
  - `facebook/mms-tts-quc-dialect_east` *(Rabinal / Joyabaj / Cubulco)*
  - `facebook/mms-tts-quc-dialect_north` *(Cunén / Uspantán border)*
- **Architecture:** Single-speaker character-level VITS (~36.3M parameters, 16,000 Hz output, HiFi-GAN decoder built in, no eSpeak/G2P required).
- **License:** **CC-BY-NC 4.0** (NonCommercial — acceptable for academic capstone & public rural school non-profit pilots; cannot be sold commercially without swapping weights later).

#### Jetson Orin Nano 8 GB Fit
- **RAM/VRAM:** **~180–240 MB RAM** on CPU (`sherpa-onnx`, 6 threads) — identical memory class to Utz'tutor's measured `Sherpa-ONNX` (`+192 MB RAM / +2.8 MB VRAM`). **100% co-resident with the SLM.**
- **Disk:** ~145 MB FP32 ONNX per voice (~37–45 MB if dynamically INT8-quantized via `onnxruntime.quantization.quantize_dynamic`; verify listening quality before shipping INT8 since aggressive INT8 can add hiss on VITS decoders).
- **Latency:** ~0.25–0.50 s warm p50 per classroom explanation (~0.04–0.07× RTF) — well under the ≤ 3.0 s SLA.
- **Peak & Sample Rate:** Native `16,000 Hz`, calibrated to `0.78` peak via existing `samples_to_wav()` (`backend/src/core/tts/audio.py:20-39`).

#### Known Limitations
- Trained on Bible audio recordings: formal, somewhat flat/solemn male/narrator prosody rather than a warm primary-school teacher.
- 16 kHz bandwidth sounds slightly less crisp than Spanish 22.05 / 24 kHz engines.
- `vocab.txt` has **no digits** and uses a specific apostrophe character — requires Section 5.3 normalization.
- `facebook/mms-tts` checkpoints are PyTorch weights; they must be exported once (on a dev PC) to `sherpa-onnx`-compatible ONNX + `tokens.txt` (or fetched from verified community ONNX exports such as `willwade/mms-tts-multilingual-models-onnx`, pinned by commit SHA & checksum).

#### Implementation Plan (Option 1)
1. **Step 1 — Offline ONNX Export & Metadata Pipeline (Dev PC, 1 day):**
   - Add an offline conversion script `tools/voice_models/export_mms_onnx.py` following `k2-fsa/sherpa-onnx`'s official `vits-mms.py` recipe:
     - Download `G_100000.pth`, `config.json`, `vocab.txt` (or HF safetensors via `transformers.VitsModel`) for `quc-dialect_central` (plus optional `east`/`north`) and `kek`, pinned to exact HF commit SHAs.
     - Export `model.onnx` (opset 13–17) and generate `tokens.txt` (`<char> <id>` per line from `vocab.txt`).
     - Embed mandatory `sherpa-onnx` MMS metadata in `model.onnx`:
       ```python
       meta_data = {
           "model_type": "vits",
           "comment": "mms",
           "frontend": "characters",
           "add_blank": str(int(hps.data.add_blank)),
           "n_speakers": "1",
           "sample_rate": "16000",
           "language": lang_code,  # "quc" or "kek"
       }
       ```
     - Inspect each model's `vocab.txt` and record the exact glottal-stop glyph and allowed character set in a small `vocab_profile.json` next to `tokens.txt`.
     - Test FP32 vs INT8 dynamic quantization on 10 real Kʼicheʼ and Qʼeqchiʼ classroom sentences; keep FP32 (~145 MB) if INT8 degrades glottal stops.
   - Host/package the exported `.onnx` + `tokens.txt` bundles and register them in `tools/voice_models/catalog.py` + `tiers.py` under a new `--download-models mayan` (and `all`) tier with SHA-256 verification.
2. **Step 2 — Character-Mode Support in `SherpaBackend` (1 day):**
   - Inspect ONNX metadata once at `preload()` (not per request; fix M7) to detect whether a model is `comment == "mms"` / `frontend == "characters"` vs Piper (`has_espeak == "1"`).
   - In `backend/src/core/tts/engines/sherpa/engine.py`:
     - Keep `SherpaBackend` ≤ 150 LoC by splitting path/metadata inspection into `engines/sherpa/models.py`.
     - When `self._is_character_frontend` is True, synthesize using `sherpa_onnx.GenerationConfig(sid=0, speed=...)` **without** calling `phoneme_generation_config(...)` (no eSpeak!).
     - Support per-language Sherpa model configs: `TTS_SHERPA_MODEL_QUC` (default `vits-mms-quc-dialect_central/model.onnx`) and `TTS_SHERPA_MODEL_KEK` (default `vits-mms-kek/model.onnx`).
3. **Step 3 — Text Localization & Mayan Normalizer (2–3 days):**
   - Execute Section 5.1, 5.2 (Tier A: 33 misconception translations + framing scripts), and 5.3 (ALMG glottal canonicalization + number-to-word expansion for `quc` and `kek`).
4. **Step 4 — Router Integration & Single-Resident Enforcement (1 day):**
   - In `core/tts/router/mayan_selection.py`, set the Mayan `auto` tier order to:
     - `quc`: `sherpa` (MMS/Piper) → `piper` → `espeak` (only if `TTS_VOICE_QUC` set) → `503`.
     - `kek`: `sherpa` (MMS/Piper) → `piper` → `espeak` (only if `TTS_VOICE_KEK` set) → `503`.
   - Verify `POST /api/v1/tts/load` with `{"lang": "quc"}` or `{"lang": "kek"}` evicts any resident Spanish Qwen3-TTS daemon cleanly and preloads the ~190 MB MMS model.
5. **Step 5 — Quality Gate, Jetson Benchmark & Native-Speaker Audit (1–2 days):**
   - Add unit tests (mocked `sherpa_onnx`, character-mode bypass, glottal preservation, digit-to-word conversion, 503 isolation) maintaining 100% statement coverage and ≤ 150/300 LoC policy.
   - Run `tools/benchmark/tts/metrics.py` on the Jetson Orin Nano (25 W mode) alongside Ollama/llama-server to record real cold load, warm p50/p95, RTF, and UMA RAM peak.
   - Have at least one native Kʼicheʼ speaker and one native Qʼeqchiʼ speaker listen to all 33 synthesized misconception scripts to catch mispronounced math terms or dialect mismatches.

---

### Option 2: Fine-Tuned MMS-TTS VITS on Native Classroom Teacher Audio → ONNX in `sherpa-onnx`

**Verdict:** **Best quality-to-effort upgrade over Option 1.** Keeps the exact same **~200 MB co-resident Jetson footprint** and zero backend runtime changes after Option 1, while replacing the stiff Bible-reading voice with a warm, child-friendly local primary-school teacher voice.

#### Why It Works with Tiny Data
- Meta's MMS checkpoints already learned Kʼicheʼ (`quc`) and Qʼeqchiʼ (`kek`) character-to-acoustics alignments and glottal/ejective phonology.
- Using Hugging Face's **`ylacombe/finetune-hf-vits`** recipe, adapting a pre-trained MMS VITS model to a new speaker and classroom domain requires only **80–400 clean single-speaker clips (~15–60 minutes of audio)** — far less than training from scratch!

#### Jetson Orin Nano 8 GB Fit
- **Identical to Option 1:** **~180–240 MB RAM**, ~145 MB FP32 ONNX (~40 MB INT8), ~0.3–0.5 s latency, **100% co-resident with SLM**.
- **Training hardware:** Runs **offline** on a dev/cloud GPU (1× T4/L4/RTX 3090/4090, 16–24 GB VRAM) in ~1–3 hours — **never** trained on the Jetson.
- **License:** Inherits **CC-BY-NC 4.0** from the Meta MMS base checkpoint.

#### Implementation Plan (Option 2)
1. **Step 1 — Classroom Recording Script Design (2 days):**
   - Draft 200–350 short sentences (4–9 seconds each) in ALMG-standardized Kʼicheʼ and/or Qʼeqchiʼ with an EBI educator:
     - All 33 diagnostic misconception explanations and classroom framing phrases.
     - Mayan numbers `0–100`, fractions, operations, and encouraging classroom phrases (*"Utz!"*, *"Chatchoman chi rij…"* / *"Us!"*, *"Kʼoxla…"*).
     - ~100 phonetically balanced primary-school sentences ensuring heavy coverage of ejectives (`bʼ, chʼ, kʼ, qʼ, tʼ, tzʼ`), uvular `q`, and long vs. short vowels (especially critical in Qʼeqchiʼ!).
2. **Step 2 — Studio/Quiet-Room Recording & Preprocessing (2–3 days):**
   - Record one consistent, warm native teacher per language (44.1/48 kHz WAV mono, cardioid mic or quiet room, pop filter), then resample to **16,000 Hz mono PCM** matching MMS, trim leading/trailing silence (< 200 ms), normalize loudness (-20 LUFS), and review every transcript character-for-character against `vocab.txt`.
   - Hold out 10% of clips (including unseen math explanations) as a validation set.
3. **Step 3 — Fine-Tuning via `ylacombe/finetune-hf-vits` (1 day on cloud GPU):**
   - Format dataset as `metadata.csv` (`file_name,transcription`) + WAV folder.
   - Start from `facebook/mms-tts-quc-dialect_central` (or `facebook/mms-tts-kek`), low learning rate (`~1e-4` to `2e-4`), 50–150 epochs, monitoring discriminator/mel loss and listening to held-out samples every 25 epochs to prevent overfitting on small data.
4. **Step 4 — Export to `sherpa-onnx` ONNX & Drop-In Replacement (0.5 day):**
   - Run the same Option 1 ONNX exporter (`export_mms_onnx.py`) on the fine-tuned HF checkpoint to produce `vits-mms-quc-teacher/model.onnx` + `tokens.txt` (with identical `"comment": "mms"`, `"frontend": "characters"`, `"sample_rate": "16000"` metadata).
5. **Step 5 — A/B Listening Evaluation & Deployment (1 day):**
   - Compare base MMS vs fine-tuned MMS using `tools/benchmark/tts/ab.py` with native teachers (intelligibility of ejectives, naturalness, clarity for 6–12 year-olds).
   - Publish pinned artifact checksum in `tools/voice_models/catalog.py`; zero backend code changes needed beyond pointing `TTS_SHERPA_MODEL_QUC` / `TTS_SHERPA_MODEL_KEK` at the new file.

---

### Option 3: Custom Piper VITS (22.05 kHz) Trained via `OHF-Voice/piper1-gpl`

**Verdict:** **Best long-term, commercial-safe, co-resident neural architecture.** Produces crisp **22.05 kHz** audio, avoids Meta MMS's NonCommercial CC-BY-NC restriction, stays under **~205 MB RAM**, and drops directly into Utz'tutor's pre-designed `PiperBackend` (`TTS_PIPER_MODEL_QUC`) and `SherpaBackend` slots.

#### Two Phonemization Modes (Key Decision)
- **Mode 3A — Grapheme Mode (`"phoneme_type": "text"`):**
  - Bypasses `espeak-ng` completely; characters map directly to `phoneme_id_map`.
  - Works identically for **both Kʼicheʼ and Qʼeqchiʼ** because ALMG orthography is highly phonemic.
  - Needs ~2–4 hours of clean single-speaker audio (transfer-learning from an open-licensed Spanish Piper medium checkpoint like `es_ES-sharvard-medium` or `es_MX-ald-medium` with `--ckpt_path` so acoustic/HiFi-GAN layers converge quickly).
- **Mode 3B — eSpeak-ng Phoneme Mode (`"phoneme_type": "espeak"`):**
  - For **Kʼicheʼ (`quc`)**: `piper-tts` already bundles `espeak-ng-data/lang/myn/quc`! Training with `--data.espeak_voice quc` works out of the box and generalizes better on smaller datasets (~1–2 hours), though you should first verify `quc_rules` handles all ALMG ejectives accurately.
  - For **Qʼeqchiʼ (`kek`)**: Requires authoring and compiling `kek_rules` + `kek_list` in `espeak-ng` (see Option 7) before preprocessing.

#### Open Datasets to Combine with Teacher Recordings
- **Kʼicheʼ (`quc`):** Mozilla Common Voice / Mozilla Data Collective / ELARSpeech (~15.3 h total multi-speaker — filter for cleanest top speakers and denoise), SIL `bloom-speech`, COERLL Kʼicheʼ corpus, plus 1–2 h self-recorded single-speaker teacher audio (single-speaker fine-tune stage at the end gives best quality).
- **Qʼeqchiʼ (`kek`):** SIL `bloom-speech` + self-recorded single-speaker teacher audio (1.5–3 h; clean single-speaker studio audio beats 10 h of noisy crowdsourced audio for VITS!).

#### Jetson Orin Nano 8 GB Fit
- **RAM/VRAM:** **~180–205 MB RAM** (identical to measured Piper `+202 MB` / Sherpa `+192 MB`). **100% co-resident with SLM.**
- **Disk:** ~65–76 MB FP32 ONNX + ~5 KB `.onnx.json`.
- **Latency:** **~0.40 s warm p50** (~0.05× RTF), 22,050 Hz output.
- **License:** Clean (you own weights trained on your own / CC0 / CC-BY audio + open MIT/Apache Spanish base checkpoint; `piper1-gpl` training code is GPLv3, exported ONNX weights carry your data license).

#### Implementation Plan (Option 3)
1. **Step 1 — Dataset Curation & Cleaning (1–2 weeks):**
   - Assemble 1.5–4 hours of clean 22,050 Hz mono audio per language (single speaker preferred, or multi-speaker pretrain followed by 30–60 min single-speaker teacher fine-tune).
   - Normalize ALMG orthography (consistent apostrophe, double-vowel length markers in Qʼeqchiʼ) into `metadata.csv` (`utt001.wav|Transcript`).
   - Run automated SNR & clipping checks; manually audit 5% of transcripts.
2. **Step 2 — Transfer-Learning in `OHF-Voice/piper1-gpl` (2–4 days on cloud GPU):**
   - Clone `OHF-Voice/piper1-gpl`, build `monotonic_align`, and initialize from an open Spanish `medium` (22.05 kHz) `.ckpt` (warm-starting decoder/flow while re-initializing the symbol embedding table if switching to `"phoneme_type": "text"`).
   - Train 1,500–3,000 epochs (or until mel reconstruction & alignment stabilize), evaluating held-out classroom explanations.
   - Export ONNX via `python3 -m piper.train.export_onnx` → produces `quc_GT-teacher-medium.onnx` + `.onnx.json` (and `kek_GT-teacher-medium.onnx` + `.onnx.json`).
3. **Step 3 — Runtime Wiring for Grapheme-Mode Piper & `kek` Support (1 day):**
   - **Backend `PiperBackend` (`engines/piper/engine.py`):** Extend `_resolve_voice_and_speaker()` to resolve `"kek"` (`TTS_PIPER_MODEL_KEK`, `TTS_PIPER_SPEAKER_KEK`) alongside `"quc"` and `"es"`. Note: `piper-tts` natively reads `"phoneme_type": "text"` from `.onnx.json`!
   - **Backend `SherpaBackend` (`engines/sherpa/`):** Update `tools/voice_models/sherpa.py:_build_vits_metadata()` so models with `"phoneme_type": "text"` set `"has_espeak": "0"` and `"frontend": "characters"`, and skip `phoneme_generation_config` at synthesis time.
   - Keep `TTS_PIPER_LENGTH_SCALE=1.12`, `NOISE_SCALE=0.35`, `NOISE_W_SCALE=0.45` tuned for primary-school diction (verify optimal values for Mayan cadence).
4. **Step 4 — Model Packaging, Tests & Jetson Verification (1 day):**
   - Register pinned URLs + SHA-256 hashes in `tools/voice_models/catalog.py`.
   - Run full backend quality gate (`ruff`, `pytest` 100% coverage, modularity check) + Jetson `tools/benchmark/tts/metrics.py` & `ab.py`.

---

### Option 4: Pre-Recorded Native Teacher Audio Bank + Hybrid Neural Fallback

**Verdict:** **Highest authenticity for rural primary classrooms, 0 MB RAM overhead, and astonishingly practical given Utz'tutor's finite curriculum.**

#### Why This Fits Utz'tutor Uniquely Well
Utz'tutor is **not** an arbitrary open-domain audiobook reader. Its >51% spoken intervention explains one of **33 diagnostic misconceptions** (`CURRICULUM_TAXONOMY`) across **66 seed questions** (and 320 pool questions).
- Recording **33 misconception explanations** in Kʼicheʼ and 33 in Qʼeqchiʼ takes **~15 minutes per teacher** and covers **every possible topic and even brand-new LLM-generated questions** (at the misconception level)!
- Recording **66 seed questions × 3 distractors = 198 question-specific clips** takes **~1.5 hours per teacher** and covers the entire shipped question bank word-for-word!
- For any newly generated or teacher-edited question without a matching audio clip, the router seamlessly falls back to **Option 1/2/3** (neural TTS).

#### Jetson Orin Nano 8 GB Fit
- **RAM/VRAM:** **~0 MB model RAM / 0 MB VRAM** (reads a ~150 KB clip from disk; zero neural inference). **Co-resident with everything!**
- **Disk:**
  - 200 clips × 8 s @ 22.05 kHz 16-bit WAV ≈ **~68 MB** per language (zero decoding overhead, matches `audio/wav` API directly).
  - Or stored as 24 kbps Opus/OGG ≈ **~5 MB** per language (decoded/served as `audio/ogg` or pre-decoded to WAV on install).
- **Latency:** **< 20 ms** (essentially instant!).
- **Audio Quality:** **10/10** — genuine human warmth, exact dialectal ejectives, natural encouragement for children.

#### Implementation Plan (Option 4)
1. **Step 1 — Recording Pack & Manifest Schema (1 week with EBI educators):**
   - Finalize Kʼicheʼ & Qʼeqchiʼ scripts for:
     - Level 1 (Minimum Viable): 33 misconception-slug explanations (`misconceptions/{slug}.wav`).
     - Level 2 (Full Curated Bank): 198 seed-question distractor clips (`questions/{question_id}_{option}.wav`).
   - Record with native teachers (written consent & fair compensation), trim silence, peak-calibrate every WAV to `0.78` (`core/tts/audio.py:calibrate_wav_peak`) so volume matches neural fallbacks seamlessly.
   - Place under `/opt/utztutor/models/tts/recorded/{lang}/` with a `manifest.json` mapping keys → filenames + SHA-256 hashes + speaker attribution.
2. **Step 2 — Implement `RecordedAudioBackend` (1 day):**
   - Create `backend/src/core/tts/engines/recorded/` (`engine.py` ≤ 100 LoC, `manifest.py` ≤ 80 LoC) implementing `TTSBackend`:
     - `is_available(lang)` checks that `manifest.json` exists and has clips for `lang`.
     - `is_loaded()` returns `True` (or manifest cached in a tiny dict, < 100 KB RAM).
     - `synthesize(text, voice)` resolves a lookup key (e.g., passed via structured key or `(question_id, option)` / `misconception_slug` from `api/session/speech.py`), returning calibrated WAV bytes or raising `TTSUnavailableError` on cache miss so the router drops cleanly to neural TTS!
3. **Step 3 — Hybrid Routing in `api/session/speech.py` & `TTSRouter` (1 day):**
   - Before synthesizing `script` dynamically when `lang in ("quc", "kek")`, check `recorded_lookup(lang, question.id, decision.dominant_distractor, decision.misconception)`:
     - Hit → return pre-recorded teacher WAV immediately (< 20 ms, `X-TTS-Source: recorded`).
     - Miss (e.g., fresh LLM-generated question or teacher-edited explanation) → dispatch to neural tier (Option 1/2/3).
   - Keep `POST /api/v1/tts/preview` playing a dedicated `preview.wav` clip for the recorded tier.
4. **Step 4 — Packaging & Quality Gate (0.5 day):**
   - Add `--download-models recorded-mayan` (or bundle tarballs in Ansible `infra/ansible/tasks/`) and unit tests covering hit, miss→neural fallback, and missing-pack `503`.

---

### Option 5: Fine-Tuned `Qwen3-TTS-12Hz-0.6B-Base` (or `1.7B-Base`) GGUF in Existing `llama-tts-daemon`

**Verdict:** **Highest neural naturalness & bilingual code-switching potential** (24 kHz), reusing Utz'tutor's custom-patched CUDA `llama-tts-daemon`. **Requires Tier-B Phased Lifecycle** (SLM unloaded) and 1–5 hours of clean training data.

#### Critical Architectural Insights for Jetson Orin Nano
1. **Prefer `Qwen3-TTS-12Hz-0.6B-Base` over `1.7B-Base` for Mayan deployment:**
   - Utz'tutor measured `Qwen3-TTS-12Hz-1.7B-Base-Q4_K_M` at **~3.3 GB resident / ~3.4 GB peak** on Jetson Orin Nano (`docs/architecture/voice-feedback.md:101`).
   - Fine-tuning **`Qwen/Qwen3-TTS-12Hz-0.6B-Base`** and quantizing to `Q4_K_M` cuts Talker weights roughly in third (~350–400 MB vs 982 MiB) and reduces KV-cache/work buffers, bringing total resident memory to roughly **~1.6–1.9 GB** with `TTS_QWEN_BATCH=128` + `TTS_QWEN_CONTEXT=1024` + your existing `0002-qwen-tok-embd-rows.patch`!
   - Generation speed also improves over 1.7B's 1.05× RTF, bringing Jetson synthesis comfortably faster than real time.
2. **Why Fine-Tuning (SFT) is Mandatory (Zero-Shot Cloning Won't Work Alone):**
   - Base Qwen3-TTS only natively knows 10 major languages (Spanish, English, Chinese, etc.). Passing a 3-second Kʼicheʼ WAV via `TTS_QWEN_SPEAKER_FILE` without fine-tuning will copy the teacher's *timbre* while reading Kʼicheʼ text with a Spanish accent and mangling glottal stops (`qʼ, tzʼ, bʼ`).
   - Supervised fine-tuning via the official **`QwenLM/Qwen3-TTS/finetuning/sft_12hz.py`** teaches the Talker transformer Mayan orthography → 12 Hz discrete acoustic codes while keeping the pretrained 12 Hz speech tokenizer/vocoder intact.
   - **Bilingual bonus:** Mixing ~20–30% Spanish math audio with Kʼicheʼ/Qʼeqchiʼ during SFT lets a **single** 0.6B/1.7B GGUF model speak smooth bilingual code-switched explanations (e.g., Kʼicheʼ explanation + Spanish math terms) without unloading/reloading models!

#### Jetson Orin Nano 8 GB Fit
- **RAM/VRAM (CUDA, `-ngl 99`, `TTS_QWEN_BATCH=128`, `TTS_QWEN_CONTEXT=1024`):**
  - `0.6B-Base Q4_K_M`: **~1.6–1.9 GB** shared LPDDR5 (**Tier B — Phased**; unload SLM during voting).
  - `1.7B-Base Q4_K_M`: **~3.3–3.4 GB** shared LPDDR5 (**Tier B — Phased**; measured in repo).
- **Disk:** ~0.8 GB (0.6B GGUF + mmproj Q8_0) or ~1.5 GB (1.7B).
- **License:** **Apache 2.0** (commercial-safe!).

#### Implementation Plan (Option 5)
1. **Step 1 — Prerequisite: Wire Automatic SLM↔TTS Phased Lifecycle on Jetson (2 days):**
   - Fix `backend/src/api/llm/proxy.py` so `POST /api/v1/llm/unload` works with **Ollama** (sending `POST /api/generate` with `keep_alive: 0` when `SLM_BASE_URL` targets `:11434`, since `infra/ansible/group_vars/all.yml:67` runs Ollama on the kit and `/models/unload` returns 404) as well as `llama-server`.
   - Hook quiz session transitions (`modes/quiz/session/session_manager.py`): when a round opens for voting, optionally unload SLM and preload the selected TTS engine if it is a heavy (Tier-B) backend; when returning to quiz generation, unload Qwen TTS before calling SLM.
   - Fix `suggestions.md` M5 (daemon request lock) and M6 (daemon stderr handling).
2. **Step 2 — Dataset Preparation & Official Qwen3-TTS SFT (1–2 weeks + cloud GPU):**
   - Collect 1–5 hours of clean 24 kHz single-speaker Kʼicheʼ and/or Qʼeqchiʼ audio (optionally mixed with Spanish classroom audio for bilingual code-switching).
   - Build `train_raw.jsonl` (`{"audio": ..., "text": ..., "ref_audio": ...}` using one consistent reference clip).
   - Extract 12 Hz discrete codes via `QwenLM/Qwen3-TTS/finetuning/prepare_data.py`.
   - Run `sft_12hz.py` on `Qwen/Qwen3-TTS-12Hz-0.6B-Base` (cloud GPU: 24–40 GB VRAM, `lr=2e-6`, 5–15 epochs). Evaluate on unseen classroom math scripts.
3. **Step 3 — GGUF Conversion & Daemon Compatibility Verification (2 days):**
   - Convert fine-tuned Talker + audio projector to GGUF (`Q4_K_M` Talker + `Q8_0` mmproj) using `llama.cpp`'s Qwen3-TTS conversion toolchain pinned to `b11002` (matching `tools/llama_tts_daemon/`).
   - Verify both patches (`0001-llama-tts-daemon-mode.patch` and `0002-qwen-tok-embd-rows.patch`) load the 0.6B GGUF cleanly on Jetson CUDA and check whether `llama-tts-daemon` `--tts-lang` accepts custom language prompts or passes a neutral/mapped tag for the fine-tuned Mayan checkpoint.
4. **Step 4 — Backend `QwenBackend` Multi-Language Refactor (1–2 days):**
   - Fix `backend/src/core/tts/engines/qwen/engine.py:108` (`len(voice) == 2` bug) to accept 3-letter ISO 639-3 codes (`quc`, `kek`).
   - Parameterize `resolve_qwen_paths(lang)` (`engines/qwen/models.py`) to resolve per-language or bilingual GGUF paths (`TTS_QWEN_GGUF_PATH_QUC`, `TTS_QWEN_GGUF_PATH_KEK`) instead of hardcoding `Qwen3-TTS-12Hz-1.7B-Base-Q4_K_M.gguf`.
   - Register `qwen3-tts` in `core/tts/router/mayan_selection.py` only when a Mayan-trained GGUF is explicitly configured (never route `quc`/`kek` to the Spanish-only Base checkpoint!).
5. **Step 5 — Jetson Profiling & Memory Soak Test (1 day):**
   - Measure 0.6B resident/peak UMA RAM, cold start, prompt eval, generation RTF, and 10-round SLM↔TTS swap stability on the Jetson Orin Nano at 25 W.

---

### Option 6: Lightweight Flow-Matching TTS (`Matcha-TTS` in `sherpa-onnx`, `ZipVoice` TensorRT, or `F5-TTS-ONNX`)

**Verdict:** **Strong modern alternative to VITS if training from scratch/small data** — flow-matching training is significantly more stable than GAN-based VITS (no discriminator collapse), and ZipVoice/F5-TTS skip explicit G2P entirely.

#### Three Sub-Options Sized for Jetson Orin Nano 8 GB

- **6A. `Matcha-TTS` + `Vocos` in `sherpa-onnx` (Co-Resident Champion — ~220–350 MB RAM):**
  - ~18–25M parameter Conditional Flow Matching acoustic model + ~13M Vocos 22.05 kHz vocoder; only **5 Euler steps** needed.
  - **Already natively supported in `sherpa-onnx`** (`sherpa_onnx.OfflineTtsMatchaModelConfig`) — zero PyTorch on the Jetson!
  - Runs faster-than-real-time on Orin Nano CPU (~0.3–0.6 s) and stays **co-resident with the SLM (Tier A)**.
  - Train on 1–5 h of Kʼicheʼ/Qʼeqchiʼ audio (character/grapheme mode or `espeak-ng quc` phonemes), export acoustic + Vocos to ONNX.
- **6B. `ZipVoice` (k2-fsa, 123M CFM) via `sherpa-onnx` or TensorRT FP16 (Phased — ~0.7–1.2 GB):**
  - Built by the exact same `k2-fsa` team behind `sherpa-onnx`! Supports zero-shot/few-shot voice cloning, 3-file ONNX export (encoder, decoder, vocoder), **and** official TensorRT export (`zipvoice.bin.tensorrt_export`, ~2× faster than PyTorch on NVIDIA GPUs).
  - Base checkpoints are Chinese/English, so Mayan requires fine-tuning on ~2–10 h of Kʼicheʼ/Qʼeqchiʼ audio (character-based, no G2P needed!).
- **6C. `F5-TTS` (336M DiT CFM) via `F5-TTS-ONNX` / TensorRT FP16 (Phased — ~1.4–2.2 GB):**
  - Proven community track record adapting to low-resource languages (e.g., Kurdish Sorani, Lingala) with ~5–10 hours of audio and **no forced aligner / no G2P**.
  - On Jetson Orin Nano, PyTorch F5-TTS is too slow/heavy; requires optimized ONNX (`F5-TTS-ONNX` graph cleanup) or pre-built FP16 TensorRT engines with Sway Sampling (16–24 steps).

> **Jetson Orin Nano TensorRT Build Warning (6B/6C):** Never run TensorRT auto-tuning inline inside the FastAPI Python process on an 8 GB Jetson — TRT's workspace tuner can spike RAM and trigger the OOM killer. Always stop the GUI/kiosk, ensure NVMe swap is enabled, and pre-build `.engine` files offline via `trtexec` during kit provisioning (`infra/ansible/`).

#### Implementation Plan (Option 6 — Focusing on 6A Matcha-TTS / 6B ZipVoice)
1. **Step 1 — Select Sub-Variant & Prepare Corpus (1–2 weeks):**
   - Choose **6A (`Matcha-TTS`)** if you require **Tier-A co-residency** with the SLM and minimal disk (~100 MB).
   - Choose **6B (`ZipVoice`)** if you want **teacher voice cloning** from a 5–10 s reference clip and already have Tier-B phased swapping.
   - Prepare 2–8 hours of clean 22.05/24 kHz ALMG-normalized single/multi-speaker audio.
2. **Step 2 — Offline Training / Fine-Tuning on Cloud GPU (2–5 days):**
   - Train Matcha-TTS (`shivammehta25/Matcha-TTS`) or fine-tune ZipVoice (`k2-fsa/ZipVoice`) on cloud GPU until mel/flow loss converges and held-out Mayan sentences pass native-speaker intelligibility checks.
3. **Step 3 — ONNX / TensorRT Export (1–2 days):**
   - For **6A:** Export Matcha acoustic ONNX (5-step) + `vocos-22khz-univ.onnx` + `tokens.txt` following `k2-fsa/sherpa-onnx` Matcha docs.
   - For **6B:** Export ZipVoice encoder/decoder/vocoder ONNX (or compile FP16 `.engine` directly on the target Jetson via `trtexec` with headless mode + NVMe swap).
4. **Step 4 — Backend Integration (`core/tts/engines/matcha/` or `zipvoice/`) (1–2 days):**
   - Implement a focused `TTSBackend` module (≤ 150 LoC) wrapping `sherpa_onnx.OfflineTtsMatchaModelConfig` (or `OfflineTtsZipVoiceModelConfig`) using the exact pattern of `engines/kokoro/engine.py`.
   - Register engine in `TTSRouter`, `tts_settings.py`, `tools/voice_models/`, and `mayan_selection.py`.
5. **Step 5 — Jetson Benchmarking & Soak Testing (1 day):**
   - Profile cold load, warm p50/p95, RTF, peak UMA RAM, and peak amplitude calibration (`0.78`) using `tools/benchmark/tts/metrics.py`.

---

### Option 7: `eSpeak-ng` Formant Synthesis (`quc` Built-In Today + Custom Compiled `kek`)

**Verdict:** **Emergency safety net & free G2P phonemizer only — NOT recommended as primary classroom audio.** Fits in ~10 MB RAM and gives Kʼicheʼ a working zero-model fallback in minutes.

#### Key Findings
- **Kʼicheʼ (`quc`) is already present** in `espeak-ng >= 1.51` (and already verified inside `.cache/venv/Lib/site-packages/piper/espeak-ng-data/lang/myn/quc`). Ubuntu 22.04 / JetPack 6 installs `espeak-ng` via `infra/ansible/group_vars/all.yml:26`.
- **Qʼeqchiʼ (`kek`) is NOT built in**, but Qʼeqchiʼ shares almost the exact same ALMG phoneme inventory as Kʼicheʼ (`bʼ, chʼ, kʼ, qʼ, tʼ, tzʼ, q, x, j`), differing primarily in **phonemic vowel length** (`aa, ee, ii, oo, uu`), syllable-final stress details, and vocabulary exceptions. Authoring `kek_rules` + `kek_list` derived from `quc_rules` and compiling with `espeak-ng --compile=kek` takes ~2–3 days with a linguist/native speaker.
- **Acoustic reality:** Formant synthesis sounds metallic and struggles with the sharp acoustic burst of uvular ejectives (`qʼ`) and voiced bilabial implosive (`bʼ` [ɓ]). Keep it strictly as the **ultimate safety net** (identical to its role for Spanish) or as a **phonemizer for Option 3 (Piper)**.

#### Jetson Orin Nano 8 GB Fit
- **RAM/VRAM:** **~9–10 MB RAM, 0 MB VRAM** (measured in repo: `+8.9 MB`). **100% co-resident.**
- **Disk:** < 1 MB.
- **Latency:** **~0.29 s** (~0.03× RTF).

#### Implementation Plan (Option 7)
1. **Step 1 — Verify `quc` on Jetson & Enable Opt-In Fallback (0.5 day):**
   - Run `espeak-ng --voices=myn` and `espeak-ng -v quc "Utz iwach, kʼo jun kʼaxkʼolil." -w test.wav` on the Jetson.
   - Audit pronunciation of ejectives (`bʼ, chʼ, kʼ, qʼ, tʼ, tzʼ`) with a native Kʼicheʼ speaker; verify whether `espeak-ng` expects `'` (U+0027) vs `ʼ` (U+02BC) in `quc_rules` and ensure `text_mayan.py` normalizes accordingly.
   - Update `.env.example` and `constants.py:36` comment (reflecting that `quc` IS shipped in `espeak-ng` as `status testing`, keeping `DEFAULT_TTS_VOICE_QUC="quc"` opt-in or fallback-only behind neural engines).
2. **Step 2 — Optional Custom `kek` eSpeak-ng Dictionary (2–3 days):**
   - Store `infra/espeak/kek_rules`, `infra/espeak/kek_list`, and `infra/espeak/lang_kek` in the repo (derived from `espeak-ng`'s `quc` files, adding Qʼeqchiʼ long-vowel durations `aa/ee/ii/oo/uu`, `h` handling, and Qʼeqchiʼ numbers/math words).
   - Add an Ansible task in `infra/ansible/tasks/packages.yml` to compile and install `kek_dict` via `espeak-ng --compile=kek`.
   - Set `TTS_VOICE_KEK=kek` and wire `resolve_voice()` in `core/tts/engines/espeak/cli.py` (while also adding `@functools.cache` to `_installed_voices()` per `suggestions.md` L15).
3. **Step 3 — Strict Fallback Ordering (0.5 day):**
   - Ensure `eSpeak` is NEVER selected over Recorded (Option 4), Sherpa/MMS (Options 1–2), or Piper (Option 3) in `auto` mode — only used when explicitly requested or when no neural/recorded asset is installed.

---

## 7. Recommended Phased Roadmap for Utz'tutor

Combining options gives the fastest path to a real bilingual rural classroom pilot without ever threatening the 8 GB Jetson Orin Nano memory ceiling:

```text
Phase 1 (Week 1 — Ship Both Languages Offline Today, Tier A Co-Resident)
├── Shared Prerequisites (§5): quc + kek API/UI, 33-slug human translations, Mayan math/glottal normalizer
├── Option 1: Export facebook/mms-tts-quc-dialect_central & facebook/mms-tts-kek → sherpa-onnx (~190 MB RAM)
└── Option 7: Enable bundled espeak-ng 'quc' as ultimate fallback (~9 MB RAM)

Phase 2 (Weeks 2–3 — Authentic Teacher Voice, Tier A Co-Resident)
├── Option 4: Record native Kʼicheʼ & Qʼeqchiʼ teachers for the 33 misconceptions + 66 seed questions (Tier-0, 0 MB RAM)
└── Option 2: Fine-tune MMS-TTS on 15–45 min of those recordings → drop-in ONNX for dynamic LLM questions (~190 MB RAM)

Phase 3 (Post-Pilot — Commercial-Safe 22–24 kHz Upgrade)
├── Path A (Co-Resident, Recommended): Option 3 — Train 22.05 kHz Piper VITS in grapheme mode (clean license, ~200 MB RAM)
└── Path B (Phased Highest Prosody):   Option 5 — Fine-tune Qwen3-TTS-0.6B-Base → GGUF in llama-tts-daemon (~1.7 GB RAM, needs SLM swap)
```

### Target Mayan Auto-Engine Ladder in `TTSRouter`
```text
Recorded Teacher Bank (Option 4, <20 ms, 0 MB)
  └─ miss on dynamic/edited question ─▶ Sherpa-ONNX MMS / Piper (Options 1–3, ~0.4 s, ~200 MB)
       └─ unavailable ─▶ Qwen3-TTS Mayan GGUF (Option 5, optional Tier-B)
            └─ unavailable ─▶ eSpeak-ng quc/kek (Option 7, ~0.3 s, ~9 MB, only if voice installed)
                 └─ unavailable ─▶ HTTP 503 (never silently speaks Spanish!)
```

---

## 8. Evaluated & Ruled Out Options (Why Not on Jetson Orin Nano)

| Candidate | Why Ruled Out for Utz'tutor on Jetson Orin Nano (8 GB) |
| :--- | :--- |
| **IMS-Toucan (`ToucanTTS`)** | Supports 7,000+ languages via articulatory features, **but** requires a heavy PyTorch + `torchaudio` + `transphone` runtime (~1.5–3 GB RAM on Jetson ARM64, no official `sherpa-onnx` export), and zero-shot Mayan prosody without fine-tuning is noticeably robotic/accented. Useful only as an *offline workstation* research baseline, not on the classroom box. |
| **Coqui `XTTS-v2`** | Upstream archived/unmaintained, CPML non-commercial license, ~2.5–4 GB VRAM + PyTorch overhead, no native `quc`/`kek` support, high latency on Orin Nano. |
| **Kokoro-82M** *(already in repo for Spanish)* | Tiny (~488 MB RAM), **but** tightly locked to fixed `misaki`/eSpeak phoneme tables for 8 high-resource languages and lacks an established low-resource fine-tuning pipeline for Mayan phonologies. |
| **Fish Speech / Orpheus 3B / Spark-TTS / CosyVoice-3B** | 1.5–4+ GB VRAM + PyTorch/heavy LLM runtimes crowd out the 8 GB UMA envelope and offer **zero** out-of-the-box Kʼicheʼ or Qʼeqchiʼ coverage. |
| **Cloud TTS APIs (Google / Azure / ElevenLabs)** | Violates Utz'tutor's hard **100% offline rural classroom** mandate — and none natively support Kʼicheʼ or Qʼeqchiʼ anyway. |
| **Meta `NLLB-200` (for text translation)** | Frequently misassumed to cover Mayan languages, **but `quc_Latn` and `kek_Latn` are NOT in the official 200-language release**. Use curated human translations (§5.2) or `google/madlad400-3b-mt` INT8 on CTranslate2 instead. |

---

## 9. Linguistic, Cultural & Practical Checklist for Guatemalan Classrooms

1. **ALMG Standard Orthography:** Follow the *Academia de Lenguas Mayas de Guatemala* (ALMG) alphabet for both Kʼicheʼ and Qʼeqchiʼ. Ensure every stage — DB storage, Pydantic sanitizers (`modes/quiz/contracts/sanitizer.py`), `normalize_for_speech()`, and `tokens.txt` — preserves glottalized consonants (`bʼ, chʼ, kʼ, qʼ, tʼ, tzʼ`), uvular `q`, and Qʼeqchiʼ double-vowel length distinctions (`aa, ee, ii, oo, uu`).
2. **Dialect Matching Per School:**
   - **Kʼicheʼ (`quc`)** varies significantly across regions (e.g., Totonicapán/Quetzaltenango Central vs. Rabinal/Joyabaj East vs. Cunén North). MMS-TTS offers `central`, `east`, and `north` checkpoints — let `infra/ansible/kit.yml` select the dialect matching the target school's municipality!
   - **Qʼeqchiʼ (`kek`)** is more mutually intelligible across Alta Verapaz (Cobán/Carchá), Petén, and Izabal, though Cobán/Alta Verapaz standard is the broadest default for classroom materials.
3. **Classroom Math Register (EBI Reality Check):** Consult local EBI teachers before finalizing `text_mayan.py` number expansion: some primary classrooms teach vigesimal Mayan numerals (*jun, kebʼ, oxibʼ…*), while others use Spanish numerals for multi-digit numbers and fractions inside a Kʼicheʼ/Qʼeqchiʼ sentence. Supporting a config toggle (`MAYAN_NUMERAL_STYLE=mayan|spanish_loan`) avoids forcing the wrong classroom norm.
4. **Licensing Clarity:**
   - **Non-commercial / capstone / public-school grant pilots:** Options 1 & 2 (MMS-TTS, **CC-BY-NC 4.0**) + Option 4 (teacher recordings) are legally clean.
   - **Any commercial or paid-kit distribution:** Must graduate to **Option 3** (Piper VITS), **Option 4** (recorded bank), **Option 5** (Qwen3-TTS Apache 2.0), or **Option 6** (Matcha-TTS / ZipVoice MIT/Apache).
5. **Speaker Consent & Community Co-Design:** Any native teacher recorded for Options 2, 3, 4, 5, or 6 should sign plain-language informed consent (Spanish + Kʼicheʼ/Qʼeqchiʼ) specifying offline classroom use, voice-cloning/model-training permissions, attribution, and compensation, and teachers should review generated clips before students hear them.
