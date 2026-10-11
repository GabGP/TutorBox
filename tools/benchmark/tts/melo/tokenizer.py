"""Converts Spanish text into the blank-interspersed phoneme token sequence MeloTTS expects."""

from __future__ import annotations

import re

from tools.benchmark.tts.melo.phonetics import PHONETIC_OVERRIDES

WORD_PATTERN: str = r"[\wáéíóúñ]+|[.,:;!?]"
SPACE_SYMBOL: str = "SP"
BLANK_TOKEN_ID: int = 0


def text_to_token_ids(
    text: str,
    token_ids_by_symbol: dict[str, int],
    lexicon: dict[str, list[str]],
) -> list[int]:
    """Converts text into token ids with a blank id before, between and after every symbol."""
    words = re.findall(WORD_PATTERN, text.lower())
    token_sequence: list[int] = []
    space_token_id = token_ids_by_symbol.get(SPACE_SYMBOL, 0)

    for word in words:
        if word in token_ids_by_symbol:
            token_sequence.append(token_ids_by_symbol[word])
        elif word in PHONETIC_OVERRIDES:
            for phoneme in PHONETIC_OVERRIDES[word]:
                if phoneme in token_ids_by_symbol:
                    token_sequence.append(token_ids_by_symbol[phoneme])
        elif word in lexicon:
            for phoneme in lexicon[word]:
                if phoneme in token_ids_by_symbol:
                    token_sequence.append(token_ids_by_symbol[phoneme])
        else:
            for character in word:
                if character in token_ids_by_symbol:
                    token_sequence.append(token_ids_by_symbol[character])
        token_sequence.append(space_token_id)

    interspersed_token_ids = [BLANK_TOKEN_ID] * (len(token_sequence) * 2 + 1)
    interspersed_token_ids[1::2] = token_sequence
    return interspersed_token_ids
