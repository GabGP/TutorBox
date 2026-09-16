# Qwen-GGUF Engine Profile (Spike Candidate 5)

## Architectural Profile
- **Architecture**: 0.6B Q8_0 or F16 quantized model executing via GGUF/llama.cpp edge runtime.
- **Target Language**: Multilingual including native Spanish speech tokens.
- **License**: Apache 2.0
- **Resource Constraints**:
  - Fail Condition: Warm latency on Jetson Orin Nano CPU > 3.0s or memory footprint > 1.0 GB RAM.
  - Evaluation Timebox: 1 engineering day max.

## Evaluation Focus
- Assess viability of running transformer-based autoregressive TTS alongside SLM on edge hardware.
- If latency or memory exceeds appliance SLAs, immediately mark as failed and preserve Piper baseline.
