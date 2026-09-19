# TutorBox llama.cpp Patch Management & Build Protocol

This directory contains upstream patches applied to [`llama.cpp`](https://github.com/ggerganov/llama.cpp) to enable low-latency, persistent in-memory speech synthesis for TutorBox.

---

## 1. Pinned Upstream Baseline

* **Repository**: `https://github.com/ggerganov/llama.cpp.git`
* **Pinned Release / Tag**: `b11002`
* **Upstream Git Commit**: `83078fec0`
* **License**: MIT License (Preserved in [`LICENSE-llama-cpp`](./LICENSE-llama-cpp) and deployed to [`.cache/bin/llama.cpp/LICENSE-llama-cpp`](../../.cache/bin/llama.cpp/LICENSE-llama-cpp)).

---

## 2. Included Patches

### `0001-llama-tts-daemon-mode.patch`
* **Target File**: `tools/tts/tts.cpp`
* **Purpose**: Adds an interactive line-delimited JSON daemon loop (`--daemon`) to `llama-tts`.
* **Rationale**:
  - In upstream one-shot mode (`llama-tts -m ... -p "..." -o out.wav`), the binary must parse GGUF weights, allocate CUDA VRAM buffers, and initialize the computation graph on **every single speech utterance**, incurring a cold start overhead of ~1.2–1.8 seconds.
  - The `--daemon` mode initializes the 1.7B acoustic model, text tokenizer, and vocoder **once** and remains resident in memory.
  - It listens on `stdin` for JSON requests and outputs JSON responses to `stdout`:
    ```json
    // Request (stdin newline-delimited)
    {"text": "El perimetro es la suma de los lados.", "out_path": "/path/to/output.wav"}

    // Response (stdout newline-delimited)
    {"status": "ok", "out_path": "/path/to/output.wav", "duration_ms": 1940}
    ```
  - Eliminates all model-reloading latency, delivering instant response times.

---

## 3. Automated Build & Compilation

To build and install the daemon binary into `.cache/bin/llama.cpp/`, run:

```bash
# Standard automated build (detects CUDA or falls back to CPU, multithreaded Ninja build)
python tools/llama-tts-daemon/build.py

# Force clean re-clone and re-compilation
python tools/llama-tts-daemon/build.py --force

# Force CPU-only build (disables -DGGML_CUDA=ON)
python tools/llama-tts-daemon/build.py --cpu-only
```

Alternatively, `run.py` can automatically invoke compilation:
```bash
# Build before launching appliance
python run.py --build-llama

# Clean rebuild before launching
python run.py --force-build-llama
```

---

## 4. Manual Reproduction Steps

If compiling manually from source without the helper script:

1. **Clone pinned upstream release**:
   ```bash
   git clone --depth 1 --branch b11002 https://github.com/ggerganov/llama.cpp.git .cache/build/llama.cpp
   cd .cache/build/llama.cpp
   ```

2. **Apply TutorBox daemon patch**:
   ```bash
   git apply ../../../tools/llama-tts-daemon/0001-llama-tts-daemon-mode.patch
   ```

3. **Configure & Build with CMake (Multithreaded)**:
   ```bash
   # With NVIDIA CUDA
   cmake -B build -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_SERVER=OFF -G Ninja
   cmake --build build --target llama-tts --config Release --parallel 16

   # CPU Only
   cmake -B build -DGGML_CUDA=OFF -DCMAKE_BUILD_TYPE=Release -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_SERVER=OFF -G Ninja
   cmake --build build --target llama-tts --config Release --parallel 16
   ```

4. **Install Binaries, DLLs, and License**:
   ```bash
   mkdir -p ../../bin/llama.cpp/
   cp build/bin/llama-tts ../../bin/llama.cpp/llama-tts-daemon
   cp build/bin/*.dll ../../bin/llama.cpp/
   cp ../../../tools/llama-tts-daemon/LICENSE-llama-cpp ../../bin/llama.cpp/LICENSE-llama-cpp
   ```

---

## 5. License & Attribution Notice

`llama.cpp` and its tools are licensed under the MIT License by Georgi Gerganov and contributors. All modifications made in this directory respect upstream license conditions. The MIT license text is bundled alongside binary distributions in `.cache/bin/llama.cpp/LICENSE-llama-cpp`.
