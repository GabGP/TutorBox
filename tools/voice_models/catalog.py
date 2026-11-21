"""Where each Utz'tutor voice model is published and what it is called on disk."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_MODELS_DIR = ROOT_DIR / ".cache" / "models" / "tts"

PIPER_BASE_URL = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/sharvard/medium"
)
PIPER_ONNX_NAME = "es_ES-sharvard-medium.onnx"
PIPER_CONFIG_NAME = "es_ES-sharvard-medium.onnx.json"
PIPER_TOKENS_NAME = "tokens_es_ES-sharvard-medium.txt"
PIPER_SHERPA_NAME = "es_ES-sharvard-medium.sherpa.onnx"

KOKORO_DIR_NAME = "kokoro-int8-multi-lang-v1_0"
KOKORO_ARCHIVE_NAME = f"{KOKORO_DIR_NAME}.tar.bz2"
KOKORO_TAR_URL = (
    "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/"
    f"{KOKORO_ARCHIVE_NAME}"
)
KOKORO_VOICES_NAME = "voices.bin"
KOKORO_MODEL_NAME = "model.onnx"
KOKORO_INT8_MODEL_NAME = "model.int8.onnx"

QWEN_BASE_URL = (
    "https://huggingface.co/ggml-org/Qwen3-TTS-12Hz-1.7B-Base-GGUF/resolve/main"
)
QWEN_DIR_NAME = "qwen"
QWEN_GGUF_NAME = "Qwen3-TTS-12Hz-1.7B-Base-Q4_K_M.gguf"
QWEN_MMPROJ_NAME = "mmproj-Qwen3-TTS-12Hz-1.7B-Base-Q8_0.gguf"

# Meta MMS-TTS (VITS) checkpoints for the Mayan audio guides on the downloads page,
# read by pwa/tts-tests/generate_tts.py. Each lives in mms/<checkpoint name>/.
MMS_BASE_URL = "https://huggingface.co/facebook"
MMS_DIR_NAME = "mms"
MMS_KICHE_MODEL = "mms-tts-quc-dialect_central"
MMS_QEQCHI_MODEL = "mms-tts-kek"
MMS_MODELS = (MMS_KICHE_MODEL, MMS_QEQCHI_MODEL)
MMS_WEIGHTS_NAME = "model.safetensors"
MMS_FILE_NAMES = (
    "config.json",
    "vocab.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    MMS_WEIGHTS_NAME,
)
