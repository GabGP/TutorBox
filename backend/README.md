# TutorBox Backend

FastAPI application running on the NVIDIA Jetson Orin Nano.

## Components
* **FastAPI Server**: REST API and WebSocket endpoints for student interactions.
* **Pedagogical Logic**: Socratic hint escalation ladder state machine.
* **Math Validation**: Deterministic SymPy engine & containment guardrail.
* **ASR Service**: Meta Omnilingual ASR 300M CTC int8 (`sherpa-onnx`) for K'iche' speech-to-text.
* **Database**: SQLite with idempotent SQL migrations.
