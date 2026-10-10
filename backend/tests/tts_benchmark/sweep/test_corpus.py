"""Verifies corpus loading, line cleanup and the evaluation-text selection."""

import pytest

from tools.benchmark.tts.sweep.corpus import (
    FIRST_CORPUS_ENTRY_INDEX,
    load_corpus_texts,
    select_evaluation_texts,
)


def write_corpus(corpus_path, content: str) -> None:
    """Writes the corpus file as UTF-8 text."""
    corpus_path.write_text(content, encoding="utf-8")


def test_blank_and_whitespace_lines_are_skipped_and_lines_are_stripped(tmp_path):
    """Verifies blank lines are dropped and kept lines lose outer whitespace."""
    corpus_path = tmp_path / "es_math.txt"
    write_corpus(corpus_path, "  Hola mundo  \n\n   \n\tBuenos días\t\n")
    assert load_corpus_texts(corpus_path) == ["Hola mundo", "Buenos días"]


def test_accented_characters_survive_utf8_reading(tmp_path):
    """Verifies accented Spanish text is read back unchanged from a UTF-8 file."""
    corpus_path = tmp_path / "es_math.txt"
    write_corpus(corpus_path, "Atención\n")
    assert load_corpus_texts(corpus_path) == ["Atención"]


def test_file_with_only_blank_lines_gives_an_empty_list(tmp_path):
    """Verifies a corpus made only of blank or whitespace lines yields no texts."""
    corpus_path = tmp_path / "es_math.txt"
    write_corpus(corpus_path, "\n   \n\t\n")
    assert load_corpus_texts(corpus_path) == []


def test_corpus_path_given_as_a_string_is_accepted(tmp_path):
    """Verifies a str path loads the same texts as a Path object."""
    corpus_path = tmp_path / "es_math.txt"
    write_corpus(corpus_path, "uno\ndos\n")
    assert load_corpus_texts(str(corpus_path)) == ["uno", "dos"]


def test_missing_corpus_file_raises_file_not_found(tmp_path):
    """Verifies a missing corpus file propagates FileNotFoundError to the caller."""
    with pytest.raises(FileNotFoundError):
        load_corpus_texts(tmp_path / "absent.txt")


def test_first_corpus_entry_index_is_zero():
    """Verifies the evaluation fallback points at the first corpus entry."""
    assert FIRST_CORPUS_ENTRY_INDEX == 0


def test_default_selection_keeps_only_the_first_text():
    """Verifies without all_texts only the first corpus entry is evaluated."""
    texts = ["uno", "dos", "tres"]
    assert select_evaluation_texts(texts, all_texts=False) == [(0, "uno")]


def test_all_texts_selection_pairs_every_text_with_its_index():
    """Verifies all_texts evaluates every corpus entry with its index, in order."""
    texts = ["uno", "dos", "tres"]
    assert select_evaluation_texts(texts, all_texts=True) == [
        (0, "uno"),
        (1, "dos"),
        (2, "tres"),
    ]
