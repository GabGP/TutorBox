"""Unit tests for offline TTS text preparation (src/core/tts/text.py)."""

from core.tts.text import normalize_for_speech


def test_normalize_reads_oral_fractions() -> None:
    """Verifies common primary-school fractions use singular/plural spoken forms."""
    assert normalize_for_speech("1/2") == "un medio"
    assert normalize_for_speech("3/2") == "3 medios"
    assert normalize_for_speech("1/3") == "un tercio"
    assert normalize_for_speech("2/3") == "2 tercios"
    assert normalize_for_speech("1/4") == "un cuarto"
    assert normalize_for_speech("3/4") == "3 cuartos"
    assert normalize_for_speech("1/5") == "un quinto"
    assert normalize_for_speech("4/5") == "4 quintos"
    assert normalize_for_speech("1/6") == "un sexto"
    assert normalize_for_speech("5/6") == "5 sextos"
    assert normalize_for_speech("1/7") == "un séptimo"
    assert normalize_for_speech("1/8") == "un octavo"
    assert normalize_for_speech("6/8") == "6 octavos"
    assert normalize_for_speech("1/9") == "un noveno"
    assert normalize_for_speech("1/10") == "un décimo"
    assert normalize_for_speech("7/10") == "7 décimos"
    # Denominators > 10 fallback to "sobre"
    assert normalize_for_speech("11/15") == "11 sobre 15"


def test_normalize_reads_latex_fractions() -> None:
    """Verifies LaTeX \\frac{num}{den} structures are expanded to oral Spanish."""
    assert normalize_for_speech(r"\frac{1}{2}") == "un medio"
    assert normalize_for_speech(r"\frac{3}{4}") == "3 cuartos"
    assert normalize_for_speech(r"\frac{11}{15}") == "11 sobre 15"
    assert (
        normalize_for_speech(r"Calcula \frac{1}{4} + \frac{2}{4}")
        == "Calcula un cuarto + 2 cuartos"
    )


def test_normalize_reads_exponents_and_superscripts() -> None:
    """Verifies caret and unicode exponents are rewritten into oral Spanish."""
    assert normalize_for_speech("x^2") == "x al cuadrado"
    assert normalize_for_speech("x^3") == "x al cubo"
    assert normalize_for_speech("x^4") == "x elevado a la 4"
    assert normalize_for_speech("x²") == "x al cuadrado"
    assert normalize_for_speech("y³") == "y al cubo"
    assert (
        normalize_for_speech("Resuelve x^2 + 4 = 13")
        == "Resuelve x al cuadrado + 4 igual a 13"
    )


def test_normalize_reads_negative_numbers_and_subtraction() -> None:
    """Verifies negative numbers use 'menos' without breaking binary subtraction."""
    assert normalize_for_speech("-5") == "menos 5"
    assert normalize_for_speech("x = -3") == "x igual a menos 3"
    assert normalize_for_speech("(-2)") == "(menos 2)"
    assert normalize_for_speech("-3/4") == "menos 3 cuartos"
    assert normalize_for_speech("9-4") == "9 menos 4"
    assert normalize_for_speech("9 - 4") == "9 menos 4"


def test_normalize_reads_latex_symbols_and_strips_delimiters() -> None:
    """Verifies LaTeX operators become words and math delimiters are cleaned."""
    assert normalize_for_speech(r"x \cdot y") == "x por y"
    assert normalize_for_speech(r"x \times y") == "x por y"
    assert normalize_for_speech(r"a \pm b") == "a más o menos b"
    assert normalize_for_speech(r"x \le 5") == "x menor o igual que 5"
    assert normalize_for_speech(r"x \ge 5") == "x mayor o igual que 5"
    assert normalize_for_speech(r"x \neq 0") == "x diferente de 0"
    assert normalize_for_speech(r"$x^2 = 9$") == "x al cuadrado igual a 9"


def test_normalize_reads_arithmetic_operators() -> None:
    """Verifies standard arithmetic symbols become the words a teacher would say."""
    assert normalize_for_speech("3*4") == "3 por 4"
    assert normalize_for_speech("3 × 4") == "3 por 4"
    assert normalize_for_speech("12 ÷ 4") == "12 sobre 4"
    assert normalize_for_speech("2+3") == "2 más 3"
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
    assert (
        normalize_for_speech("uno dos tres cuatro cinco", max_chars=12)
        == "uno dos tres"
    )
    assert normalize_for_speech("uno dos tresmilcuatro", max_chars=12) == "uno dos"


def test_normalize_handles_empty_and_unbounded_input() -> None:
    """Verifies empty text yields empty output and max_chars=0 disables truncation."""
    assert normalize_for_speech("") == ""
    long_text = "palabra " * 200
    assert len(normalize_for_speech(long_text, max_chars=0)) > 600
