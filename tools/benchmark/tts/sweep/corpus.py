"""Corpus loading and evaluation-text selection for the TTS sweep."""

from __future__ import annotations

from pathlib import Path

FIRST_CORPUS_ENTRY_INDEX: int = 0


def load_corpus_texts(corpus_path: Path | str) -> list[str]:
    """Reads the corpus as UTF-8 and returns its non-blank lines, stripped."""
    corpus_content = Path(corpus_path).read_text(encoding="utf-8")
    return [line.strip() for line in corpus_content.splitlines() if line.strip()]


def select_evaluation_texts(texts: list[str], all_texts: bool) -> list[tuple[int, str]]:
    """Selects (index, text) pairs; the caller guarantees texts is not empty."""
    if all_texts:
        return list(enumerate(texts))
    return [(FIRST_CORPUS_ENTRY_INDEX, texts[FIRST_CORPUS_ENTRY_INDEX])]
