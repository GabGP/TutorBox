"""Generate the Kʼicheʼ and Qʼeqchiʼ APK install guides with Meta MMS-TTS, offline.

Setup, once, from the repository root (the same steps as the Spanish voices):
    ./run.py --download-models mayan    # installs the Python packages and both models

Then:
    python pwa/tts-tests/generate_tts.py            # WAVs next to this script
    python pwa/tts-tests/generate_tts.py --publish  # also the MP3s on /descargas/

The models come from .cache/models/tts/mms/ (tools/voice_models). The guide text,
in the orthography MMS expects, is in guide_clauses.py; instructions.md explains it.
"""

import argparse
import importlib.util
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parents[1]
DOWNLOADS_AUDIO_DIR = ROOT_DIR / "pwa" / "tareas" / "descargas" / "audio"
REQUIRED_PACKAGES = ("torch", "transformers", "scipy", "lameenc")
SETUP_HINT = "Run from the repository root: ./run.py --download-models mayan"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
# The models are read from local folders: never wait on the Hugging Face Hub.
os.environ.setdefault("HF_HUB_OFFLINE", "1")

from guide_clauses import KICHE_STEPS, QEQCHI_STEPS

from tools.voice_models.catalog import (
    DEFAULT_MODELS_DIR,
    MMS_KICHE_MODEL,
    MMS_QEQCHI_MODEL,
)
from tools.voice_models.mms import mms_model_dir, mms_models_present

# (label, checkpoint, clauses, WAV name next to this script, MP3 name on /descargas/audio/)
GUIDES = (
    ("Kʼicheʼ", MMS_KICHE_MODEL, KICHE_STEPS, "kiche_instruction.wav", "kiche.mp3"),
    (
        "Qʼeqchiʼ",
        MMS_QEQCHI_MODEL,
        QEQCHI_STEPS,
        "qeqchi_instruction.wav",
        "qeqchi.mp3",
    ),
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--publish",
        action="store_true",
        help=f"also write the MP3s the downloads page plays ({DOWNLOADS_AUDIO_DIR})",
    )
    parser.add_argument(
        "--models-dir",
        type=Path,
        default=DEFAULT_MODELS_DIR,
        help="voice models directory (default: .cache/models/tts)",
    )
    return parser.parse_args()


def check_setup(models_dir: Path) -> None:
    """Stops with the setup command when a package or a model is missing."""
    missing = [name for name in REQUIRED_PACKAGES if not importlib.util.find_spec(name)]
    if missing:
        sys.exit(f"Missing Python packages: {', '.join(missing)}. {SETUP_HINT}")
    if not mms_models_present(models_dir):
        sys.exit(f"MMS models not found in {models_dir / 'mms'}. {SETUP_HINT}")


def main() -> None:
    args = parse_arguments()
    check_setup(args.models_dir)

    # Imported only after check_setup: these modules need torch and transformers.
    from synthesis import (
        load_voice,
        synthesize_steps,
        validate_vocab,
        write_mp3,
        write_wav,
    )

    for label, model_name, steps, wav_name, mp3_name in GUIDES:
        print(f"Loading {label} voice ({model_name})...")
        voice = load_voice(mms_model_dir(args.models_dir, model_name))
        validate_vocab(voice, steps, label)
        print(f"Generating {label} instructions...")
        pcm16, sampling_rate = synthesize_steps(voice, steps)
        write_wav(pcm16, sampling_rate, SCRIPT_DIR / wav_name)
        if args.publish:
            write_mp3(pcm16, sampling_rate, DOWNLOADS_AUDIO_DIR / mp3_name)


if __name__ == "__main__":
    main()
