# Moss-Nano ONNX Engine Profile (Spike Candidate 2)

## Architectural Profile
- **Architecture**: Lightweight 100M parameter Transformer/Diffusion TTS compiled directly to ONNX.
- **Runtime**: Pure ONNX Runtime CPU execution (zero PyTorch / heavy Python framework dependencies).
- **Target Language**: Native Spanish support out of the box.
- **License**: Apache 2.0
- **Audio Output**: 48,000 Hz high-fidelity synthesis.
- **Resource Constraints**:
  - Fail Condition: Fails jury listening test against Piper Sharvard or exhibits higher latency without pedagogical acoustic gain.

## Evaluation Focus
- Assess acoustic naturalness of 48 kHz output when played over classroom speaker setups.
- Profile 4-core CPU execution time on the Jetson Orin Nano architecture.
