"""Text preparation for offline TTS: ensures math explanations sound natural.

Rewrites fractions, arithmetic symbols, exponents, negative signs, and LaTeX notation
into the conversational Spanish words a primary-school teacher uses in class.
"""

import re

__all__ = ["normalize_for_speech"]

_FRACTION_DENOMINATORS: dict[int, tuple[str, str]] = {
    2: ("medio", "medios"),
    3: ("tercio", "tercios"),
    4: ("cuarto", "cuartos"),
    5: ("quinto", "quintos"),
    6: ("sexto", "sextos"),
    7: ("séptimo", "séptimos"),
    8: ("octavo", "octavos"),
    9: ("noveno", "novenos"),
    10: ("décimo", "décimos"),
}

_LATEX_FRAC = re.compile(r"\\frac\{(\d+)\}\{(\d+)\}")
_PLAIN_FRAC = re.compile(r"(?<!\w)(\d+)\s*/\s*(\d+)(?!\w)")
_EXP_2 = re.compile(r"(\b\w+)\^2(?!\d)|(\b\w+)²")
_EXP_3 = re.compile(r"(\b\w+)\^3(?!\d)|(\b\w+)³")
_EXP_N = re.compile(r"(\b\w+)\^(\d+)")
_NEG_NUM = re.compile(r"(^|[(\s=])\s*[-−]\s*(?=\d)")

_LATEX_SYMBOLS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\\(?:cdot|times)\b"), " por "),
    (re.compile(r"\\div\b"), " sobre "),
    (re.compile(r"\\pm\b"), " más o menos "),
    (re.compile(r"\\(?:le|leq)\b"), " menor o igual que "),
    (re.compile(r"\\(?:ge|geq)\b"), " mayor o igual que "),
    (re.compile(r"\\neq\b"), " diferente de "),
)

_MATH_REWRITES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?<=\d)\s*÷\s*(?=\d)"), " sobre "),
    (re.compile(r"(?<=\d)\s*[*×x]\s*(?=\d)"), " por "),
    (re.compile(r"(?<=\d)\s*\+\s*(?=\d)"), " más "),
    (re.compile(r"(?<=\d)\s*[-−]\s*(?=\d)"), " menos "),
    (re.compile(r"\s*=\s*"), " igual a "),
    (re.compile(r"(?<=\d)\s*%"), " por ciento"),
    (re.compile(r"(?<=\d),(?=\d)"), " coma "),
)

_MARKUP = re.compile(r"[*_`#<>\\|$]+")
_WHITESPACE = re.compile(r"\s+")
_SENTENCE_END = re.compile(r"[.!?](?=\s|$)")


def _oral_fraction(num_str: str, den_str: str) -> str:
    """Converts numeric fraction to oral Spanish (e.g. 1/4 -> un cuarto)."""
    num, den = int(num_str), int(den_str)
    if den in _FRACTION_DENOMINATORS:
        singular, plural = _FRACTION_DENOMINATORS[den]
        return f"un {singular}" if num == 1 else f"{num} {plural}"
    return f"{num} sobre {den}"


def _replace_neg_num(match: re.Match[str]) -> str:
    """Formats negative number prefixes cleanly (e.g. -5 -> menos 5)."""
    prefix = match.group(1)
    return f"{prefix}menos " if prefix in ("", "(") else f"{prefix} menos "


def _truncate(text: str, max_chars: int) -> str:
    """Cuts over-long text at the last sentence end (or word) so speech never trails off."""
    if len(text) <= max_chars:
        return text
    head = text[:max_chars]
    sentence_ends = list(_SENTENCE_END.finditer(head))
    if sentence_ends:
        return head[: sentence_ends[-1].end()].strip()
    if text[max_chars].isspace():
        return head.strip()
    last_space = head.rfind(" ")
    return (head[:last_space] if last_space > 0 else head).strip()


def normalize_for_speech(text: str, max_chars: int = 600) -> str:
    """Rewrites arithmetic, fractions, and notation as words for natural oral speech."""
    if not text:
        return ""
    spoken = str(text)
    for pattern, replacement in _LATEX_SYMBOLS:
        spoken = pattern.sub(replacement, spoken)
    spoken = _LATEX_FRAC.sub(lambda m: _oral_fraction(m.group(1), m.group(2)), spoken)
    spoken = _PLAIN_FRAC.sub(lambda m: _oral_fraction(m.group(1), m.group(2)), spoken)
    spoken = _EXP_2.sub(lambda m: f"{m.group(1) or m.group(2)} al cuadrado", spoken)
    spoken = _EXP_3.sub(lambda m: f"{m.group(1) or m.group(2)} al cubo", spoken)
    spoken = _EXP_N.sub(r"\1 elevado a la \2", spoken)
    spoken = _NEG_NUM.sub(_replace_neg_num, spoken)
    for pattern, replacement in _MATH_REWRITES:
        spoken = pattern.sub(replacement, spoken)
    spoken = _MARKUP.sub(" ", spoken)
    spoken = _WHITESPACE.sub(" ", spoken).strip()
    return _truncate(spoken, max_chars) if max_chars > 0 else spoken
