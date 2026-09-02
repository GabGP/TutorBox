"""Regular expression patterns and constants for distractor explanation auditing."""

import re

MIN_EXPLANATION_LENGTH: int = 10

RESULT_CLAIM_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"(?:obtendr[íi]as?|obtendr[íi]an?|obtiene|obtienes|obteniendo|obtuvo|obtener)"
        r"\s+(?:un\s+resultado\s+de\s+|el\s+valor\s+de\s+|[a-z]\s*=\s*)?"
        r"(-?\d+(?:[.,]\d+)?(?:/\d+)?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:da|dando|dando\s+como\s+resultado|dio)\s+"
        r"(?:un\s+resultado\s+de\s+|[a-z]\s*=\s*)?"
        r"(-?\d+(?:[.,]\d+)?(?:/\d+)?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:resultado\s+(?:es|ser[íi]a|da|de))\s+"
        r"(?:[a-z]\s*=\s*)?"
        r"(-?\d+(?:[.,]\d+)?(?:/\d+)?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:resultando\s+en|resulta\s+en)\s+"
        r"(?:[a-z]\s*=\s*)?"
        r"(-?\d+(?:[.,]\d+)?(?:/\d+)?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:queda(?:ndo)?(?:\s+la\s+ecuaci[óo]n)?(?:\s+como)?)\s+"
        r"(?:[a-z]\s*=\s*)"
        r"(-?\d+(?:[.,]\d+)?(?:/\d+)?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:lleva\s+a(?:l)?(?:\s+un\s+resultado\s+de|\s+un\s+error\s+de)?)\s+"
        r"(-?\d+(?:[.,]\d+)?(?:/\d+)?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:equivale\s+a|igual\s+a)\s+"
        r"(-?\d+(?:[.,]\d+)?(?:/\d+)?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"[\d\)]\s*[\+\-\*/÷×·]\s*[\d\(]\s*=\s*(-?\d+(?:[.,]\d+)?(?:/\d+)?)",
        re.IGNORECASE,
    ),
]

INVALID_CLAIM_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bes\s+la\s+respuesta\s+correcta\b", re.IGNORECASE),
    re.compile(r"\bes\s+la\s+opci[óo]n\s+correcta\b", re.IGNORECASE),
    re.compile(r"\bes\s+la\s+soluci[óo]n\s+correcta\b", re.IGNORECASE),
]
