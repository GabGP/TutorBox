"""Spanish number words for the MMS voices, whose alphabets have no digits.

normalize_for_speech already turns fractions, signs and percentages into words
but leaves whole numbers as digits; an MMS tokenizer would drop those silently.
"""

import re

__all__ = ["spanish_number_words", "spell_out_numbers"]

_UP_TO_TWENTY_NINE = [
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
    "dieciséis",
    "diecisiete",
    "dieciocho",
    "diecinueve",
    "veinte",
    "veintiuno",
    "veintidós",
    "veintitrés",
    "veinticuatro",
    "veinticinco",
    "veintiséis",
    "veintisiete",
    "veintiocho",
    "veintinueve",
]
_TENS = {
    3: "treinta",
    4: "cuarenta",
    5: "cincuenta",
    6: "sesenta",
    7: "setenta",
    8: "ochenta",
    9: "noventa",
}
_HUNDREDS = {
    1: "ciento",
    2: "doscientos",
    3: "trescientos",
    4: "cuatrocientos",
    5: "quinientos",
    6: "seiscientos",
    7: "setecientos",
    8: "ochocientos",
    9: "novecientos",
}
_ONE_MILLION = 1_000_000
_LARGEST_SPOKEN = 999_999_999
_DECIMAL = re.compile(r"(\d+)\.(\d+)")
_WHOLE_NUMBER = re.compile(r"\d+")


def _below_one_hundred(number: int) -> str:
    if number < len(_UP_TO_TWENTY_NINE):
        return _UP_TO_TWENTY_NINE[number]
    tens, units = divmod(number, 10)
    return _TENS[tens] + (f" y {_UP_TO_TWENTY_NINE[units]}" if units else "")


def _below_one_thousand(number: int) -> str:
    if number == 100:
        return "cien"
    hundreds, rest = divmod(number, 100)
    if not hundreds:
        return _below_one_hundred(rest)
    return _HUNDREDS[hundreds] + (f" {_below_one_hundred(rest)}" if rest else "")


def _before_a_multiplier(words: str) -> str:
    """'veintiuno mil' is said 'veintiún mil', 'uno millón' 'un millón'."""
    if words.endswith("veintiuno"):
        return words[: -len("veintiuno")] + "veintiún"
    if words.endswith("uno"):
        return words[: -len("uno")] + "un"
    return words


def spanish_number_words(number: int) -> str:
    """Whole number in Spanish words; past 999 999 999, digit by digit."""
    if number > _LARGEST_SPOKEN:
        return " ".join(_UP_TO_TWENTY_NINE[int(digit)] for digit in str(number))
    millions, below_million = divmod(number, _ONE_MILLION)
    thousands, units = divmod(below_million, 1000)
    parts: list[str] = []
    if millions:
        parts.append(
            "un millón"
            if millions == 1
            else f"{_before_a_multiplier(_below_one_thousand(millions))} millones"
        )
    if thousands:
        parts.append(
            "mil"
            if thousands == 1
            else f"{_before_a_multiplier(_below_one_thousand(thousands))} mil"
        )
    if units or not parts:
        parts.append(_below_one_thousand(units))
    return " ".join(parts)


def spell_out_numbers(text: str) -> str:
    """Replaces every number left in the text with its Spanish words."""
    text = _DECIMAL.sub(lambda match: f"{match[1]} punto {match[2]}", text)
    return _WHOLE_NUMBER.sub(lambda match: spanish_number_words(int(match[0])), text)
