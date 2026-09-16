# Kokoro-ES Engine Profile (Spike Candidate 3)

## Architectural Profile
- **Architecture**: 82M parameter StyleTTS2 variant.
- **Runtime**: ONNX Runtime or lightweight PyTorch inference.
- **Target Language**: Spanish (`lang="e"` / `es`).
- **G2P Dependency**: Relies on `espeak-ng` phonemization pipeline.
- **License**: Apache 2.0
- **Resource Constraints**:
  - Fail Condition: Fails due to anglicized Spanish phoneme drift, robotic intonation, or missing G2P rules.

## Evaluation Focus
- Validate whether the Spanish phonemization (`espeak-ng` G2P backend) produces authentic Latin American and neutral Spanish pronunciations on mathematical fractions and decimal terminology.
