"""Accent-free keyword matching and Spanish number words for the tutor guards."""

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass

__all__ = ["Folded", "fold", "spanish_words"]

_TOKEN = re.compile(r"[a-z0-9']+")
_UNITS = [
    "cero",
    "uno",
    "dos",
    "tres",
    "cuatro",
    "cinco",
    "seis",
    "siete",
    "ocho",
    "nueve",
    "diez",
    "once",
    "doce",
    "trece",
    "catorce",
    "quince",
    "dieciseis",
    "diecisiete",
    "dieciocho",
    "diecinueve",
    "veinte",
    "veintiuno",
    "veintidos",
    "veintitres",
    "veinticuatro",
    "veinticinco",
    "veintiseis",
    "veintisiete",
    "veintiocho",
    "veintinueve",
]
_TENS = [
    "_",
    "_",
    "_",
    "treinta",
    "cuarenta",
    "cincuenta",
    "sesenta",
    "setenta",
    "ochenta",
    "noventa",
]
_HUNDREDS = [
    "_",
    "ciento",
    "doscientos",
    "trescientos",
    "cuatrocientos",
    "quinientos",
    "seiscientos",
    "setecientos",
    "ochocientos",
    "novecientos",
]
# "uno"/"una"/"un" are left out on purpose: they are also articles.
_NUMBER_WORDS = frozenset(
    {w for w in _UNITS + _TENS + _HUNDREDS if w not in {"_", "uno"}}
    | {"cien", "mil", "miles", "millon", "millones"}
)


def fold(text: str) -> str:
    """Lower-cases and strips accents (and the tilde of ñ) for keyword matching."""
    text = text.replace("’", "'").replace("´", "'").lower()
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


@dataclass(frozen=True)
class Folded:
    """A message folded once, then matched against many keyword lists."""

    tokens: tuple[str, ...]

    @classmethod
    def of(cls, text: str) -> "Folded":
        return cls(tuple(_TOKEN.findall(fold(text))))

    def has(self, keyword: str) -> bool:
        """'a b' matches the phrase, 'stem*' any word starting with stem."""
        if " " in keyword:
            return f" {keyword} " in f" {' '.join(self.tokens)} "
        if keyword.endswith("*"):
            return any(token.startswith(keyword[:-1]) for token in self.tokens)
        return keyword in self.tokens

    def has_any(self, keywords: Iterable[str]) -> bool:
        return any(self.has(keyword) for keyword in keywords)

    def number_words(self) -> set[str]:
        """Spanish number words ('ocho', 'sesenta'), which can leak an answer."""
        return {token for token in self.tokens if token in _NUMBER_WORDS}


def spanish_words(value: int) -> str:
    """Writes 0-999,999 in Spanish words ('sesenta y ocho'); '' outside that range."""
    if not 0 <= value < 1_000_000:
        return ""
    if value < 1000:
        return _below_thousand(value)
    thousands, rest = divmod(value, 1000)
    head = "mil" if thousands == 1 else f"{_below_thousand(thousands)} mil"
    return head if rest == 0 else f"{head} {_below_thousand(rest)}"


def _below_thousand(value: int) -> str:
    if value < 30:
        return _UNITS[value]
    if value < 100:
        tens, unit = divmod(value, 10)
        return _TENS[tens] if unit == 0 else f"{_TENS[tens]} y {_UNITS[unit]}"
    if value == 100:
        return "cien"
    hundreds, rest = divmod(value, 100)
    head = _HUNDREDS[hundreds]
    return head if rest == 0 else f"{head} {_below_thousand(rest)}"
