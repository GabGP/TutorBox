"""Unit tests for espeak text preparation (src/core/tts/text.py)."""

from core.tts.text import normalize_for_speech


def test_normalize_reads_fractions_and_operators_as_words() -> None:
    """Verifies arithmetic symbols become the words a teacher would say."""
    assert normalize_for_speech("6/8") == "6 sobre 8"
    assert normalize_for_speech("3*4") == "3 por 4"
    assert normalize_for_speech("3 × 4") == "3 por 4"
    assert normalize_for_speech("12 ÷ 4") == "12 sobre 4"
    assert normalize_for_speech("2+3") == "2 más 3"
    assert normalize_for_speech("9-4") == "9 menos 4"
    assert normalize_for_speech("2x + 4 = 12") == "2x + 4 igual a 12"
    assert normalize_for_speech("75%") == "75 por ciento"
    assert normalize_for_speech("0,75") == "0 coma 75"


def test_normalize_keeps_hyphenated_and_worded_text_intact() -> None:
    """Verifies word hyphens and plain prose survive the math rewrites."""
    assert normalize_for_speech("pre-álgebra es fácil") == "pre-álgebra es fácil"
    assert normalize_for_speech("Dividiste sólo el numerador.") == (
        "Dividiste sólo el numerador."
    )


def test_normalize_strips_markup_and_collapses_whitespace() -> None:
    """Verifies markdown leftovers never reach the synthesizer."""
    assert normalize_for_speech("**Ojo**:\n  dividiste   mal") == "Ojo : dividiste mal"


def test_normalize_truncates_at_the_last_sentence_end() -> None:
    """Verifies over-long text is cut where a sentence ends, not mid-word."""
    text = "Primera frase. Segunda frase. Tercera frase mucho más larga que el resto."
    assert normalize_for_speech(text, max_chars=30) == "Primera frase. Segunda frase."


def test_normalize_truncates_at_a_word_when_no_sentence_end_fits() -> None:
    """Verifies a long unpunctuated explanation still ends on a whole word."""
    # the cut lands on a word boundary: the last word is kept whole
    assert (
        normalize_for_speech("uno dos tres cuatro cinco", max_chars=12)
        == "uno dos tres"
    )
    # the cut lands mid-word: that word is dropped rather than spoken half
    assert normalize_for_speech("uno dos tresmilcuatro", max_chars=12) == "uno dos"


def test_normalize_handles_empty_and_unbounded_input() -> None:
    """Verifies empty text yields empty output and max_chars=0 disables truncation."""
    assert normalize_for_speech("") == ""
    long_text = "palabra " * 200
    assert len(normalize_for_speech(long_text, max_chars=0)) > 600
