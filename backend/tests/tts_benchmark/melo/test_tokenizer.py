"""Verifies the MeloTTS text tokenizer: word rules, fallbacks, space ids and blank interspersing."""

from tools.benchmark.tts.melo.tokenizer import text_to_token_ids

# Ids are hand-picked. "ch", "q", "z", "i" and "ó" are deliberately absent so
# that dropping unknown phonemes and characters is observable.
SYMBOL_IDS = {
    "_": 0,
    "SP": 1,
    ".": 2,
    ",": 3,
    ":": 4,
    ";": 5,
    "!": 6,
    "?": 7,
    "2": 8,
    "a": 9,
    "b": 10,
    "c": 11,
    "d": 12,
    "e": 13,
    "j": 14,
    "l": 15,
    "m": 16,
    "n": 17,
    "o": 18,
    "p": 19,
    "r": 20,
    "s": 21,
    "t": 22,
    "u": 23,
    "x": 24,
}
NO_LEXICON: dict[str, list[str]] = {}
MUNDO_LEXICON = {"mundo": ["m", "u", "n", "d", "o"]}


def test_word_that_is_itself_a_symbol_uses_its_single_id():
    """Verifies a word found in the symbol table wins over its phonetic override."""
    result = text_to_token_ids("2", SYMBOL_IDS, NO_LEXICON)
    assert result == [0, 8, 0, 1, 0]


def test_phonetic_override_word_uses_its_override_phonemes():
    """Verifies a word in PHONETIC_OVERRIDES is spoken with the override phonemes."""
    result = text_to_token_ids("por", SYMBOL_IDS, NO_LEXICON)
    assert result == [0, 19, 0, 18, 0, 20, 0, 1, 0]


def test_override_phonemes_missing_from_the_table_are_dropped():
    """Verifies the override phoneme "ch" of "80" is dropped and the rest is kept."""
    result = text_to_token_ids("80", SYMBOL_IDS, NO_LEXICON)
    assert result == [0, 18, 0, 13, 0, 17, 0, 22, 0, 9, 0, 1, 0]


def test_lexicon_word_uses_its_lexicon_phonemes():
    """Verifies a word missing from the table and overrides is spoken from the lexicon."""
    result = text_to_token_ids("mundo", SYMBOL_IDS, MUNDO_LEXICON)
    assert result == [0, 16, 0, 23, 0, 17, 0, 12, 0, 18, 0, 1, 0]


def test_lexicon_phonemes_missing_from_the_table_are_dropped():
    """Verifies a lexicon phoneme absent from the table ("q") is dropped silently."""
    result = text_to_token_ids("sol", SYMBOL_IDS, {"sol": ["s", "q", "o", "l"]})
    assert result == [0, 21, 0, 18, 0, 15, 0, 1, 0]


def test_overrides_win_over_the_lexicon_for_the_same_word():
    """Verifies a word in both PHONETIC_OVERRIDES and the lexicon uses the override."""
    result = text_to_token_ids("por", SYMBOL_IDS, {"por": ["x"]})
    assert result == [0, 19, 0, 18, 0, 20, 0, 1, 0]


def test_unknown_word_falls_back_to_its_characters_and_drops_unknown_ones():
    """Verifies an unknown word is spelled letter by letter, skipping letters not in the table."""
    result = text_to_token_ids("casaz", SYMBOL_IDS, NO_LEXICON)
    assert result == [0, 11, 0, 9, 0, 21, 0, 9, 0, 1, 0]


def test_unknown_word_of_only_unknown_characters_leaves_just_the_space_id():
    """Verifies a word made only of unknown characters contributes only its space id."""
    result = text_to_token_ids("zq", SYMBOL_IDS, NO_LEXICON)
    assert result == [0, 1, 0]


def test_accented_letters_stay_inside_one_word():
    """Verifies "atención" is one word, so exactly one space id follows its phonemes."""
    result = text_to_token_ids("atención", SYMBOL_IDS, NO_LEXICON)
    assert result == [0, 9, 0, 22, 0, 13, 0, 17, 0, 21, 0, 14, 0, 18, 0, 17, 0, 1, 0]


def test_unknown_accented_letters_are_dropped_from_a_fallback_word():
    """Verifies the accented vowel of an unknown word is dropped, not split into words."""
    result = text_to_token_ids("canción", SYMBOL_IDS, NO_LEXICON)
    assert result == [0, 11, 0, 9, 0, 17, 0, 11, 0, 17, 0, 1, 0]


def test_punctuation_marks_are_words_of_their_own():
    """Verifies each of .,:;!? becomes its own word with its own space id."""
    punctuation_ids = [(".", 2), (",", 3), (":", 4), (";", 5), ("!", 6), ("?", 7)]
    for punctuation_mark, punctuation_id in punctuation_ids:
        result = text_to_token_ids(punctuation_mark, SYMBOL_IDS, NO_LEXICON)
        assert result == [0, punctuation_id, 0, 1, 0]
    result = text_to_token_ids(".,:;!?", SYMBOL_IDS, NO_LEXICON)
    assert result[0::2] == [0] * 13
    assert result[1::2] == [2, 1, 3, 1, 4, 1, 5, 1, 6, 1, 7, 1]


def test_punctuation_is_split_from_the_word_before_it():
    """Verifies "a.b" tokenizes as three words: a, ., b."""
    result = text_to_token_ids("a.b", SYMBOL_IDS, NO_LEXICON)
    assert result == [0, 9, 0, 1, 0, 2, 0, 1, 0, 10, 0, 1, 0]


def test_text_is_lower_cased_before_matching():
    """Verifies upper-case input matches the lower-case override key."""
    result = text_to_token_ids("POR", SYMBOL_IDS, NO_LEXICON)
    assert result == [0, 19, 0, 18, 0, 20, 0, 1, 0]


def test_space_id_follows_every_word_and_the_blanks_surround_them():
    """Verifies the space id comes after each word, with blanks between every id."""
    result = text_to_token_ids("por mundo", SYMBOL_IDS, MUNDO_LEXICON)
    assert result[0::2] == [0] * 11
    assert result[1::2] == [19, 18, 20, 1, 16, 23, 17, 12, 18, 1]


def test_space_id_is_zero_when_the_table_has_no_space_symbol():
    """Verifies the space id falls back to 0 when SP is missing from the table."""
    symbol_ids_without_space = {
        symbol: token_id for symbol, token_id in SYMBOL_IDS.items() if symbol != "SP"
    }
    result = text_to_token_ids("por", symbol_ids_without_space, NO_LEXICON)
    assert result == [0, 19, 0, 18, 0, 20, 0, 0, 0]


def test_result_has_a_blank_at_every_even_position_and_length_two_n_plus_one():
    """Verifies four tokens give nine ids: a blank at each even index, then the tokens."""
    result = text_to_token_ids("por", SYMBOL_IDS, NO_LEXICON)
    assert result[0::2] == [0, 0, 0, 0, 0]
    assert result[1::2] == [19, 18, 20, 1]
    assert len(result) == 2 * 4 + 1


def test_empty_text_gives_a_single_blank():
    """Verifies empty text produces just one blank id, [0]."""
    assert text_to_token_ids("", SYMBOL_IDS, NO_LEXICON) == [0]


def test_whitespace_only_text_gives_a_single_blank():
    """Verifies text with no words produces just one blank id, [0]."""
    assert text_to_token_ids("   ", SYMBOL_IDS, NO_LEXICON) == [0]
