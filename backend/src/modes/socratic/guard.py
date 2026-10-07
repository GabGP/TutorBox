"""Last guard: text from the model reaches a child only if it is safe.

`clean` removes the model's reasoning, LaTeX and Markdown so equations arrive as
plain text. `check` rejects replies that are not Spanish, talk to the teacher
instead of the child, contain rude words, give the answer away (containment.py:
digits, words, or an expression SymPy evaluates to it) or, when rewording a hint,
add a number or a calculation the hint did not have. That last rule is what makes
rewording safe: the model can only move the hint's own numbers around, so it
cannot compute anything for the child.
"""

import re

from modes.socratic.containment import expressions, leaks
from modes.socratic.curriculum import load_curriculum
from modes.socratic.lexicon import ENGLISH, ROLE_WORDS, RUDE
from modes.socratic.numbers import extract_numbers
from modes.socratic.problems import Problem
from modes.socratic.text import Folded

__all__ = ["MAX_REPLY_CHARS", "check", "clean"]

MAX_REPLY_CHARS = 320

_LATEX = (
    (re.compile(r"\\boxed\{([^{}]*)\}"), r"\1"),
    (re.compile(r"\\[dt]?frac\{([^{}]*)\}\{([^{}]*)\}"), r"\1/\2"),
    (re.compile(r"\\(?:text|mathrm|mathbf|textbf)\{([^{}]*)\}"), r"\1"),
    (re.compile(r"\\times"), "×"),
    (re.compile(r"\\div"), "÷"),
    (re.compile(r"\\cdot"), "·"),
    (re.compile(r"\\(?:left|right)|\\[()\[\]]|\$+"), ""),
)
_MARKDOWN = re.compile(r"\*\*|__|`+|^#+\s*|^\s*[-*•]\s+|^\s*\d+[.)]\s+", re.MULTILINE)
_LABEL = re.compile(
    r"^\s*(?:mensaje reescrito|respuesta|tutor|explicaci[oó]n)\s*:\s*", re.IGNORECASE
)
_QUOTES = " «»\"“”'‘’"
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_OTHER_SCRIPT = re.compile(
    r"[\u0400-\u04ff\u0590-\u06ff\u0e00-\u0e7f\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]"
)
_ROLE_LABEL = re.compile(
    r"\b(?:ni[nñ]o|alumno|estudiante|tutor|t[uú])\s*:", re.IGNORECASE
)
# Shapes no Spanish word has: 'the', 'what', 'study', 'geometry', 'counting'
# ('deshacer' and the other des + h words are Spanish).
_ENGLISH_SHAPE = re.compile(
    r"\b[a-z]*(?:th|(?<!de)sh|wh|ck|ph|w)[a-z]*\b|\b[a-z]+(?:ing|(?<!s)tion|ly)\b"
    r"|\b[a-z]*[bcdfgjklmnpqrstvxz]y\b"
)
_REPEATED_MARK = re.compile(r"([¡!¿?.])\1+")
_OPENING_GREETING = re.compile(
    r"^¡?\s*(?:hola|buen[oa]s?\s+(?:d[ií]as|tardes|noches)|saludos)\b[^.!?]*[.!?]\s*",
    re.IGNORECASE,
)


def clean(raw: str) -> str:
    """Plain text for a child: no reasoning, LaTeX, Markdown, labels or quotes."""
    text = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)
    text = text.rsplit("</think>", 1)[-1]
    if "<think>" in text:
        return ""  # the token cap stopped the model while it was still reasoning
    for pattern, replacement in _LATEX:
        text = pattern.sub(replacement, text)
    text = " ".join(_MARKDOWN.sub("", text).split())
    text = _REPEATED_MARK.sub(r"\1", _LABEL.sub("", text).strip(_QUOTES))
    text = _OPENING_GREETING.sub("", text).strip(_QUOTES)
    sentences = _SENTENCE_END.split(text)
    while len(sentences) > 1 and len(" ".join(sentences)) > MAX_REPLY_CHARS:
        sentences.pop()
    return " ".join(sentences[:3])


def check(text: str, *, mode: str, source: str, problem: Problem | None) -> list[str]:
    """Why the model's cleaned text must not be shown ([] when it is safe).

    `mode` is "rewrite" (rewording the deterministic hint `source`) or
    "explain" (answering a CNB concept question in the model's own words).
    """
    if not text:
        return ["empty"]
    folded = Folded.of(text)
    tokens = set(folded.tokens)
    issues = [
        name
        for name, failed in (
            ("script", bool(_OTHER_SCRIPT.search(text))),
            (
                "english",
                bool(tokens & ENGLISH)
                or bool(_ENGLISH_SHAPE.search(" ".join(folded.tokens))),
            ),
            ("role", bool(_ROLE_LABEL.search(text)) or folded.has_any(ROLE_WORDS)),
            ("latex", any(ch in text for ch in "\\{}$")),
            ("long", len(text) > MAX_REPLY_CHARS),
            ("rude", bool(tokens & RUDE)),
            ("leak", problem is not None and leaks(text, problem)),
        )
        if failed
    ]
    if mode == "rewrite":
        issues += _rewrite_issues(text, source, problem)
    if mode == "explain" and not (
        load_curriculum().mentions_math(folded) or extract_numbers(text)
    ):
        issues.append("off_topic")
    return issues


def _stems(text: str) -> set[str]:
    return {t[:4] for t in Folded.of(text).tokens if len(t) >= 4 and t.isalpha()}


def _rewrite_issues(text: str, source: str, problem: Problem | None) -> list[str]:
    """A rewording keeps the hint's numbers, words and question; adds no number
    and no calculation (a word problem's '12 - 5' has no target to leak, yet it
    does the child's work).

    'Words' means at least half the hint's content-word stems: a 1.5B model
    sometimes returns fluent-looking nonsense ("Mano 23 y Mano 45") instead.
    """
    said, allowed = set(extract_numbers(text)), set(extract_numbers(source))
    source_stems = _stems(source)
    issues = []
    if len(source_stems & _stems(text)) < len(source_stems) / 2:
        issues.append("drift")
    if not said <= allowed or not (
        Folded.of(text).number_words() <= Folded.of(source).number_words()
    ):
        issues.append("number")
    if not expressions(text, problem) <= expressions(source, problem):
        issues.append("expression")
    if not allowed <= said:
        issues.append("lost")
    if "?" in source and "?" not in text:
        issues.append("no_question")
    return issues
