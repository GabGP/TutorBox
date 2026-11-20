"""Generate K'iche' and Q'eqchi' APK installation audio instructions using Meta MMS TTS.

Important orthography note:
Meta's `facebook/mms-tts-quc-dialect_central` and `facebook/mms-tts-kek` models were trained
on traditional SIL/Bible orthographies rather than modern ALMG orthography:
  - Central K'iche' (`mms-tts-quc-dialect_central`):
      * Uses saltillo `ꞌ` (U+A78C) for glottal stops (ASCII `'` and `ʼ` are dropped!)
      * /k/ -> `c` (or `qu` before e/i), /k'/ -> `cꞌ` (or `qꞌu` before e/i)
      * /q/ -> `k`, /q'/ -> `kꞌ`, /ɓ/ -> `b`, /ə/ -> `ä`
  - Q'eqchi' (`mms-tts-kek`):
      * Uses ASCII `'` (U+0027) for glottal stops
      * Uses combining macron below (U+0331) for long vowels (`a̱`, `e̱`, `i̱`, `o̱`, `u̱`)
      * /w/ -> `cu` (before vowels) or `u` (syllable-final); `w` is not in the vocab!
      * /k/ -> `c` / `qu`, /k'/ -> `c'` / `q'u`, /q/ -> `k`, /q'/ -> `k'`, /ɓ/ -> `b`

Both tokenizers also strip punctuation and digits, so instructions are synthesized
clause-by-clause and joined with brief silence pauses for natural pacing.
"""

from pathlib import Path

import numpy as np
import scipy.io.wavfile
import torch
from transformers import pipeline

# Parallel step-by-step instructions (MMS-compatible orthography)
# Each item is a list of clauses for a step; shorter pause within a step, longer pause between steps.
KICHE_STEPS = [
    # Intro: This is what you do to install an application on your cell phone with an APK file.
    [
        "are waꞌ ri caban che ubanic instalar jun aplicación pa ri a celular rucꞌ jun archivo a pe ca",
    ],
    # Step 1: First, open the Files or Downloads folder on your cell phone, and look for the APK file.
    [
        "nabe — chajakaꞌ ri cꞌolibal archivos o descargas pa ri a celular",
        "xukujeꞌ chatzucuj ri archivo a pe ca",
    ],
    # Step 2: Second, tap on the APK file so the installation begins.
    [
        "ucab — chapitzꞌaꞌ pa uwiꞌ ri archivo a pe ca rech cämajix ri instalación",
    ],
    # Step 3: Third, if a message appears asking for permission, enter Settings and allow installing apps.
    [
        "urox — we cäcꞌutun jun tzij ri cutaꞌ permiso chawe",
        "chatoc pa configuración xukujeꞌ chayaꞌ kꞌij rech cuban instalar aplicaciones",
    ],
    # Step 4: Fourth, go back, tap the Install button, and wait a moment until it finishes.
    [
        "ucaj — chattzelej lok — chapitzꞌaꞌ ri botón instalar",
        "xukujeꞌ chaweyej jubikꞌ cꞌa cäqꞌuisic",
    ],
    # Step 5: Fifth, when it finishes, tap the Open button. Now you can use the application.
    [
        "uroꞌ — are tak cäqꞌuisic — chapitzꞌaꞌ ri botón abrir",
        "cämic catcuinic cacoj ri aplicación",
    ],
]

QEQCHI_STEPS = [
    # Intro: Here is how to install an application on your cell phone with an APK file.
    [
        "a'in chanru ta̱ba̱nu instalar jun aplicación sa' la̱ celular riq'uin jun archivo a pe ca",
    ],
    # Step 1: First, open the Files or Downloads folder on your cell phone, and look for the APK file.
    [
        "xbe̱n — te li carpeta archivos malaj descargas sa' la̱ celular",
        "ut sic' li archivo a pe ca",
    ],
    # Step 2: Second, tap on the APK file so the installation begins.
    [
        "xcab — pitz' sa' xbe̱n li archivo a pe ca re nak ta̱ticla̱k li instalación",
    ],
    # Step 3: Third, if it asks you for permission, enter Settings and give permission to install apps.
    [
        "rox — cui naxpatz' permiso a̱cue",
        "ocan sa' configuración ut q'ue permiso re xba̱nunquil instalar aplicaciones",
    ],
    # Step 4: Fourth, go back, tap the Install button, and wait a moment until it finishes.
    [
        "xca̱ — sutk'in chak — pitz' li botón instalar",
        "ut oybeni bayak toj re̱tal ta̱rake'k",
    ],
    # Step 5: Fifth, when it finishes, tap the Open button. Now you can use your application.
    [
        "ro' — nak ta̱rake'k — pitz' li botón abrir",
        "anakcuan naru ta̱cuocsi la̱ aplicación",
    ],
]


def validate_vocab(tts_pipe, steps: list[list[str]], label: str) -> None:
    """Verify every character is present in the model's tokenizer vocabulary."""
    vocab = tts_pipe.tokenizer.get_vocab()
    missing = set()
    for step in steps:
        for clause in step:
            for ch in clause.lower():
                if ch not in vocab:
                    missing.add(ch)
    if missing:
        raise ValueError(
            f"[{label}] Characters not in tokenizer vocab (would be silently dropped): "
            f"{sorted(missing)!r}"
        )
    print(f"[{label}] Vocabulary check passed (0 dropped characters).")


def synthesize_steps(
    tts_pipe,
    steps: list[list[str]],
    output_path: Path,
    clause_pause_sec: float = 0.35,
    step_pause_sec: float = 0.70,
    seed: int = 42,
) -> None:
    """Synthesize step-by-step instructions and save as a 16-bit PCM WAV file."""
    torch.manual_seed(seed)
    chunks: list[np.ndarray] = []
    sampling_rate = None

    for step_idx, clauses in enumerate(steps):
        for clause_idx, clause in enumerate(clauses):
            result = tts_pipe(clause)
            sampling_rate = result["sampling_rate"]
            audio = np.asarray(result["audio"][0], dtype=np.float32).squeeze()
            chunks.append(audio)

            if clause_idx < len(clauses) - 1:
                chunks.append(np.zeros(int(sampling_rate * clause_pause_sec), dtype=np.float32))

        if step_idx < len(steps) - 1:
            chunks.append(np.zeros(int(sampling_rate * step_pause_sec), dtype=np.float32))

    full_audio = np.concatenate(chunks)
    peak = float(np.max(np.abs(full_audio)))
    if peak > 0:
        full_audio = full_audio / max(peak, 1.0) * 0.95
    pcm16 = (np.clip(full_audio, -1.0, 1.0) * 32767).astype(np.int16)

    scipy.io.wavfile.write(str(output_path), rate=sampling_rate, data=pcm16)
    duration_sec = len(pcm16) / sampling_rate
    print(f"Saved {output_path.name} ({duration_sec:.2f}s @ {sampling_rate} Hz)")


def main() -> None:
    out_dir = Path(__file__).resolve().parent

    # Initialize the Text-to-Speech pipelines
    print("Loading K'iche' MMS TTS model (facebook/mms-tts-quc-dialect_central)...")
    kiche_tts = pipeline("text-to-speech", model="facebook/mms-tts-quc-dialect_central")
    validate_vocab(kiche_tts, KICHE_STEPS, "K'iche'")

    print("Loading Q'eqchi' MMS TTS model (facebook/mms-tts-kek)...")
    qeqchi_tts = pipeline("text-to-speech", model="facebook/mms-tts-kek")
    validate_vocab(qeqchi_tts, QEQCHI_STEPS, "Q'eqchi'")

    # Generate K'iche' audio
    print("Generating K'iche' instructions...")
    synthesize_steps(kiche_tts, KICHE_STEPS, out_dir / "kiche_instruction.wav")

    # Generate Q'eqchi' audio
    print("Generating Q'eqchi' instructions...")
    synthesize_steps(qeqchi_tts, QEQCHI_STEPS, out_dir / "qeqchi_instruction.wav")


if __name__ == "__main__":
    main()
