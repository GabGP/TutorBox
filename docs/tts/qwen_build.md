# Qwen3-TTS Daemon: Build, Compilation & Deployment Guide

This guide documents the architecture, compilation instructions, and reproduction steps for the **Qwen3-TTS Persistent Daemon** deployed in TutorBox.

---

## 1. Overview & Architecture

TutorBox uses **Qwen3-TTS 1.7B Base** in GGUF format as its primary Spanish acoustic model for the deterministic **>51% Rule** spoken feedback.

```text
┌─────────────────────────────────────────────────────────────┐
│                      TutorBox Backend                       │
│  (QwenDaemon / QwenVoiceEngine - FastAPI / Python Process)  │
└──────────────────────────────┬──────────────────────────────┘
                               │ Line-delimited JSON
                               │ over stdin / stdout
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 llama-tts-daemon Process                    │
│      (C++ / llama.cpp b11002 + In-Memory Daemon Patch)       │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ Loaded GGUF Weights & Context in VRAM (Persistent)  │   │
│   │ • Qwen3-TTS-12Hz-1.7B-Base-Q4_K_M.gguf (~1.1 GB)    │   │
│   │ • mmproj-Qwen3-TTS-12Hz-1.7B-Base-Q8_0.gguf (~0.9GB)│   │
│   │ • Acoustic KV Cache & Vocoder Graph (~1.2 GB)       │   │
│   └─────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
                   Direct WAV Output on Disk
```

### Why Persistent Daemon Mode?
1. **Cold Start Latency Elimination**: Upstream `llama-tts` is a one-shot CLI utility. Re-loading 2 GB of GGUF weights, rebuilding computation graphs, and initializing CUDA context on every phrase incurs **~1.5–1.8 seconds of overhead**.
2. **Resident Memory Execution**: With the daemon patch, weights remain resident in GPU VRAM / host RAM. Syntheses execute immediately with **0 ms model reloading delay**.
3. **Phased Appliance Lifecycle**: The backend controls model load/unload via `/api/v1/tts/load` and `/api/v1/tts/unload`, ensuring the 1.7B acoustic model and the 3B SLM never compete for memory on the 8 GB Jetson Orin Nano.

---

## 2. Pinned Baseline & Licensing

| Attribute | Specification |
| :--- | :--- |
| **Upstream Base** | [`ggerganov/llama.cpp`](https://github.com/ggerganov/llama.cpp) |
| **Pinned Release** | `b11002` (commit `83078fec0`) |
| **Patch Location** | [`tools/llama-tts-daemon/0001-llama-tts-daemon-mode.patch`](../../tools/llama-tts-daemon/0001-llama-tts-daemon-mode.patch) |
| **License** | MIT License ([`tools/llama-tts-daemon/LICENSE-llama-cpp`](../../tools/llama-tts-daemon/LICENSE-llama-cpp)) |
| **Installation Directory** | `.cache/bin/llama.cpp/` |

---

## 3. Host Prerequisites

### Windows Development Host
* **Compiler**: Visual Studio 2022 / Build Tools with Desktop C++ (MSVC `vcvars64.bat` is automatically resolved).
* **CMake**: Version >= 3.20 (`cmake` in PATH).
* **Ninja (Recommended)**: For fast multi-threaded builds (`ninja` in PATH).
* **Git**: Version >= 2.30 (`git` in PATH).
* **CUDA Toolkit (Optional)**: CUDA 12.x / NVCC for GPU acceleration.

### Linux / NVIDIA Jetson Orin Nano
* **Compiler**: GCC / G++ >= 11 or Clang >= 14.
* **CMake**: Version >= 3.20 (`sudo apt install cmake ninja-build`).
* **CUDA Toolkit**: JetPack 6.x (CUDA 12.2 / 12.6 included).

---

## 4. Automated Build Instructions

TutorBox includes a cross-platform Python build tool that handles cloning the pinned upstream release, applying the patch, configuring CMake, building, and installing artifacts:

```bash
# Standard automated build (detects CUDA or falls back to CPU, parallel Ninja build)
python tools/llama-tts-daemon/build.py

# Clean rebuild (deletes .cache/build/llama.cpp/build before building)
python tools/llama-tts-daemon/build.py --force

# CPU-only compilation (forces -DGGML_CUDA=OFF)
python tools/llama-tts-daemon/build.py --cpu-only
```

### Integration with `run.py`
You can trigger compilation directly through the appliance launcher:
```bash
# Build before launching appliance
python run.py --build-llama

# Clean rebuild before launching
python run.py --force-build-llama

# Check prerequisites and report daemon binary status
python run.py --check-only
```

---

## 5. Artifact Verification & Layout

After a successful build, the following files are installed into `.cache/bin/llama.cpp/`:

```text
.cache/bin/llama.cpp/
├── llama-tts-daemon (.exe)   <- Patched interactive daemon binary
├── *.dll / *.so              <- Dynamic runtime libraries (llama.dll, ggml*.dll)
└── LICENSE-llama-cpp         <- Upstream MIT license notice
```

The daemon can be verified directly:
```bash
# List available acceleration backends (CUDA / CPU)
.cache/bin/llama.cpp/llama-tts-daemon --list-devices
```

---

## 6. Spanish Phonetics & UTF-8 Normalization

To ensure correct pronunciation of Spanish acute accents (`á, é, í, ó, ú`) and tildes (`ñ`):
1. **Unicode NFC Canonical Composition**: `backend/src/core/tts/text.py` normalizes all input text via `unicodedata.normalize("NFC", text)` before passing strings to the daemon, preventing decomposed combining grapheme anomalies (`a + ́` -> `á`).
2. **Explicit UTF-8 Subprocess Communication**: On Windows, default stdio pipes use code page 1252. The daemon runner explicitly configures `encoding="utf-8", errors="replace"` on `subprocess.Popen` pipes to prevent character corruption.

---

## 7. Memory Budget & Jetson Orin Nano Deployment

| Hardware Topology | Strategy | Memory Footprint |
| :--- | :--- | :--- |
| **PC with Discrete GPU** | Concurrent VRAM residency | ~3.3 GB VRAM + ~2.9 GB RAM |
| **Jetson Orin Nano (8 GB UMA)** | Phased Lifecycle Decoupling | ~3.3 GB Shared LPDDR5 (Unloaded when SLM active) |

On the Jetson Orin Nano:
* During quiz generation, `llama-server` (SLM) is active (~4.7 GB).
* When voting opens, `POST /api/v1/llm/unload` releases the SLM.
* `POST /api/v1/tts/load` pre-warms `llama-tts-daemon` in background (~3.3 GB).
* When a >51% distractor triggers, audio generates instantly without memory contention or OOM crash.
