"""Text and math similarity normalization algorithms for quiz question deduplication."""

import re
import unicodedata
from difflib import SequenceMatcher

_REPL = {"÷": "/", "×": "*", "·": "*"}
_LATEX_REPL = {r"\cdot": "*", r"\times": "*", r"\div": "/"}


def normalize_question_text(text: str) -> str:
    """Normalizes question text for robust deduplication comparison."""
    norm = "".join(
        c
        for c in unicodedata.normalize("NFKD", text.lower())
        if not unicodedata.combining(c)
    )
    for p in ("¿", "?", "¡", "!", ":", ";", ",", "."):
        norm = norm.replace(p, " ")
    for src, tgt in {**_REPL, **_LATEX_REPL}.items():
        norm = norm.replace(src, tgt)
    return re.sub(r"\s+", " ", norm).strip()


def extract_math_core(text: str) -> str | None:
    """Extracts mathematical equation or arithmetic core without framing."""
    norm = normalize_question_text(text)
    if "=" in norm and (
        match := re.search(r"([0-9a-z\s\+\-\*/\(\)\^]+=[0-9a-z\s\+\-\*/\(\)\^]+)", norm)
    ):
        return re.sub(r"\s+", "", match.group(1))
    if arith := re.search(r"[\d\(\)][\d\s\+\-\*/\(\)\.\^%]+[\d\)]", norm):
        return re.sub(r"\s+", "", arith.group(0))
    return None


def calculate_text_similarity(text_a: str, text_b: str) -> float:
    """Computes similarity between two normalized strings."""
    if text_a == text_b:
        return 1.0
    seq_ratio = SequenceMatcher(None, text_a, text_b).ratio()
    tok_a, tok_b = set(text_a.split()), set(text_b.split())
    jaccard = len(tok_a & tok_b) / len(tok_a | tok_b) if (tok_a | tok_b) else 0.0
    return max(seq_ratio, jaccard)
