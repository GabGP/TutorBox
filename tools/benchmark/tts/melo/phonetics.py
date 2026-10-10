"""Spanish phonetic overrides for pedagogical terms, mathematical words and digits."""

from __future__ import annotations

# Phonetic overrides for common pedagogical/mathematical Spanish terms and digits
PHONETIC_OVERRIDES: dict[str, list[str]] = {
    "100": ["s", "j", "e", "n"],
    "por": ["p", "o", "r"],
    "ciento": ["s", "j", "e", "n", "t", "o"],
    "del": ["d", "e", "l"],
    "grupo": ["g", "r", "u", "p", "o"],
    "respondió": ["r", "e", "s", "p", "o", "n", "d", "j", "o"],
    "un": ["u", "n"],
    "medio": ["m", "e", "d", "j", "o"],
    "dividiste": ["d", "i", "b", "i", "d", "i", "s", "t", "e"],
    "sólo": ["s", "o", "l", "o"],
    "el": ["e", "l"],
    "numerador": ["n", "u", "m", "e", "r", "a", "d", "o", "r"],
    "denominador": ["d", "e", "n", "o", "m", "i", "n", "a", "d", "o", "r"],
    "denominadores": ["d", "e", "n", "o", "m", "i", "n", "a", "d", "o", "r", "e", "s"],
    "entre": ["e", "n", "t", "r", "e"],
    "2": ["d", "o", "s"],
    "5": ["s", "i", "n", "k", "o"],
    "60": ["s", "e", "s", "e", "n", "t", "a"],
    "80": ["o", "ch", "e", "n", "t", "a"],
    "la": ["l", "a"],
    "respuesta": ["r", "e", "s", "p", "w", "e", "s", "t", "a"],
    "correcta": ["k", "o", "r", "e", "k", "t", "a"],
    "es": ["e", "s"],
    "tres": ["t", "r", "e", "s"],
    "cuartos": ["k", "w", "a", "r", "t", "o", "s"],
    "sextos": ["s", "e", "k", "s", "t", "o", "s"],
    "tercios": ["t", "e", "r", "s", "j", "o", "s"],
    "resta": ["r", "e", "s", "t", "a"],
    "sumaste": ["s", "u", "m", "a", "s", "t", "e"],
    "confundiste": ["k", "o", "n", "f", "u", "n", "d", "i", "s", "t", "e"],
    "atención": ["a", "t", "e", "n", "s", "j", "o", "n"],
}
