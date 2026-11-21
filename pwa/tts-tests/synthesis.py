"""Turns guide clauses into audio with an MMS voice and writes it as WAV or MP3."""

from pathlib import Path

import lameenc
import numpy as np
import scipy.io.wavfile
import torch
from transformers import Pipeline, pipeline

CLAUSE_PAUSE_SECONDS = 0.35
STEP_PAUSE_SECONDS = 0.70
PEAK_LEVEL = 0.95
MP3_BIT_RATE_KBPS = 48  # Same as the guides first published on /descargas/.
MP3_ENCODER_QUALITY = 2  # LAME scale: 0 best and slowest, 9 worst and fastest.


def load_voice(model_dir: Path) -> Pipeline:
    """Loads one MMS checkpoint from its local folder, without the network."""
    return pipeline("text-to-speech", model=str(model_dir))


def validate_vocab(voice: Pipeline, steps: list[list[str]], label: str) -> None:
    """Fails when a character is missing from the vocabulary: it would be dropped."""
    vocabulary = voice.tokenizer.get_vocab()
    missing = {
        character
        for clauses in steps
        for clause in clauses
        for character in clause.lower()
        if character not in vocabulary
    }
    if missing:
        raise ValueError(
            f"[{label}] Characters not in tokenizer vocab (would be silently dropped): "
            f"{sorted(missing)!r}"
        )
    print(f"[{label}] Vocabulary check passed (0 dropped characters).")


def _silence(sampling_rate: int, seconds: float) -> np.ndarray:
    return np.zeros(int(sampling_rate * seconds), dtype=np.float32)


def synthesize_steps(
    voice: Pipeline, steps: list[list[str]], seed: int = 42
) -> tuple[np.ndarray, int]:
    """Speaks every clause with pauses between them; returns 16-bit PCM and its rate."""
    torch.manual_seed(seed)
    chunks: list[np.ndarray] = []
    sampling_rate = 0

    for step_index, clauses in enumerate(steps):
        for clause_index, clause in enumerate(clauses):
            result = voice(clause)
            sampling_rate = int(result["sampling_rate"])
            # Older transformers return shape (1, samples), newer ones (samples,).
            chunks.append(np.asarray(result["audio"], dtype=np.float32).squeeze())
            if clause_index < len(clauses) - 1:
                chunks.append(_silence(sampling_rate, CLAUSE_PAUSE_SECONDS))
        if step_index < len(steps) - 1:
            chunks.append(_silence(sampling_rate, STEP_PAUSE_SECONDS))

    full_audio = np.concatenate(chunks)
    peak = float(np.max(np.abs(full_audio)))
    if peak > 0:
        full_audio = full_audio / max(peak, 1.0) * PEAK_LEVEL
    pcm16 = (np.clip(full_audio, -1.0, 1.0) * 32767).astype(np.int16)
    return pcm16, sampling_rate


def write_wav(pcm16: np.ndarray, sampling_rate: int, output_path: Path) -> None:
    """Writes mono 16-bit PCM as a WAV file."""
    scipy.io.wavfile.write(str(output_path), rate=sampling_rate, data=pcm16)
    print(
        f"Saved {output_path} ({len(pcm16) / sampling_rate:.2f}s @ {sampling_rate} Hz)"
    )


def write_mp3(pcm16: np.ndarray, sampling_rate: int, output_path: Path) -> None:
    """Encodes mono 16-bit PCM as a small MP3 that phones play in the browser."""
    encoder = lameenc.Encoder()
    encoder.set_bit_rate(MP3_BIT_RATE_KBPS)
    encoder.set_in_sample_rate(sampling_rate)
    encoder.set_channels(1)
    encoder.set_quality(MP3_ENCODER_QUALITY)
    mp3_bytes = encoder.encode(pcm16.tobytes()) + encoder.flush()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(bytes(mp3_bytes))
    print(f"Saved {output_path} ({len(mp3_bytes) / 1024:.0f} KB)")
