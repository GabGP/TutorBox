"""Loads the MeloTTS token-id table and Spanish lexicon from their support files."""

from __future__ import annotations

from pathlib import Path


def load_token_ids(tokens_path: Path) -> dict[str, int]:
    """Maps each symbol in tokens.txt to its integer id, skipping lines without two columns."""
    token_ids_by_symbol: dict[str, int] = {}
    if not tokens_path.exists():
        return token_ids_by_symbol
    for line in tokens_path.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split()
        if len(parts) == 2:
            token_ids_by_symbol[parts[0]] = int(parts[1])
    return token_ids_by_symbol


def load_lexicon(lexicon_path: Path) -> dict[str, list[str]]:
    """Maps each lower-cased word in lexicon.txt to its phonemes, dropping the tone columns."""
    lexicon: dict[str, list[str]] = {}
    if not lexicon_path.exists():
        return lexicon
    for line in lexicon_path.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split()
        if len(parts) >= 3 and len(parts[1:]) % 2 == 0:
            phoneme_count = len(parts[1:]) // 2
            lexicon[parts[0].lower()] = parts[1 : 1 + phoneme_count]
    return lexicon
