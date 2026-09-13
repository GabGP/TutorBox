"""Text preparation for espeak: what the appliance says has to sound like a teacher.

espeak reads raw symbols literally ("6/8" becomes "seis barra ocho"), so arithmetic is
rewritten into the words a primary-school classroom uses before the text reaches the engine.
"""

import re

__all__ = ["normalize_for_speech"]

# Applied in order; every pattern is anchored on digits so words like "pre-álgebra" survive.
_MATH_REWRITES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?<=\d)\s*[/÷]\s*(?=\d)"), " sobre "),
    (re.compile(r"(?<=\d)\s*[*×x]\s*(?=\d)"), " por "),
    (re.compile(r"(?<=\d)\s*\+\s*(?=\d)"), " más "),
    (re.compile(r"(?<=\d)\s*[-−]\s*(?=\d)"), " menos "),
    (re.compile(r"\s*=\s*"), " igual a "),
    (re.compile(r"(?<=\d)\s*%"), " por ciento"),
    (re.compile(r"(?<=\d),(?=\d)"), " coma "),
)
_MARKUP = re.compile(r"[*_`#<>\\|]+")
_WHITESPACE = re.compile(r"\s+")
_SENTENCE_END = re.compile(r"[.!?](?=\s|$)")


def _truncate(text: str, max_chars: int) -> str:
    """Cuts over-long text at the last sentence end (or word) so speech never trails off."""
    if len(text) <= max_chars:
        return text
    head = text[:max_chars]
    sentence_ends = list(_SENTENCE_END.finditer(head))
    if sentence_ends:
        return head[: sentence_ends[-1].end()].strip()
    if text[max_chars].isspace():  # the cut already landed on a word boundary
        return head.strip()
    last_space = head.rfind(" ")
    return (head[:last_space] if last_space > 0 else head).strip()


def normalize_for_speech(text: str, max_chars: int = 600) -> str:
    """Rewrites arithmetic as words, drops markup, and bounds the length for espeak."""
    if not text:
        return ""
    spoken = str(text)
    for pattern, replacement in _MATH_REWRITES:  # before markup: * can mean "por"
        spoken = pattern.sub(replacement, spoken)
    spoken = _MARKUP.sub(" ", spoken)
    spoken = _WHITESPACE.sub(" ", spoken).strip()
    return _truncate(spoken, max_chars) if max_chars > 0 else spoken
