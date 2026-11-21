"""Text to MMS token ids, the way transformers' VitsTokenizer prepares them.

MMS checkpoints spell with single characters and drop everything outside their
vocabulary, punctuation included. So the text is cut at punctuation first (the
engine puts a pause there) and each clause becomes character ids with the blank
id between them (the checkpoints were trained with add_blank).
"""

import re

__all__ = ["BLANK_TOKEN_ID", "clause_token_ids", "split_clauses"]

BLANK_TOKEN_ID = 0
# Glottal stop marks: each checkpoint knows one of them (Kʼicheʼ ꞌ, Qʼeqchiʼ ').
_GLOTTAL_STOP_MARKS = ("'", "ʼ", "ꞌ", "’")
_CLAUSE_BREAK = re.compile(r"[.,;:!?¡¿()\[\]\n]+|\s—\s")
_SPACES = re.compile(r"\s+")


def split_clauses(text: str) -> list[str]:
    """Cuts text where a speaker would pause; drops empty pieces."""
    return [clause.strip() for clause in _CLAUSE_BREAK.split(text) if clause.strip()]


def _glottal_stop_in(vocabulary: dict[str, int]) -> str | None:
    return next((mark for mark in _GLOTTAL_STOP_MARKS if mark in vocabulary), None)


def _vocabulary_text(clause: str, vocabulary: dict[str, int]) -> str:
    glottal_stop = _glottal_stop_in(vocabulary)
    characters: list[str] = []
    for character in clause:
        if character not in vocabulary:
            character = character.lower()
        if character in _GLOTTAL_STOP_MARKS and glottal_stop:
            character = glottal_stop
        if character in vocabulary:
            characters.append(character)
    return _SPACES.sub(" ", "".join(characters)).strip()


def clause_token_ids(clause: str, vocabulary: dict[str, int]) -> list[int]:
    """Token ids for one clause; empty when nothing in it can be spoken."""
    spoken = _vocabulary_text(clause, vocabulary)
    if not spoken:
        return []
    token_ids = [BLANK_TOKEN_ID]
    for character in spoken:
        token_ids.extend((vocabulary[character], BLANK_TOKEN_ID))
    return token_ids
