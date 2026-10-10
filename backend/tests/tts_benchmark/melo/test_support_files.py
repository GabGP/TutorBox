"""Verifies the MeloTTS support-file loaders for tokens.txt and lexicon.txt."""

from tools.benchmark.tts.melo.support_files import load_lexicon, load_token_ids


def test_missing_tokens_file_gives_an_empty_table(tmp_path):
    """Verifies a missing tokens.txt yields an empty symbol table instead of an error."""
    assert load_token_ids(tmp_path / "tokens.txt") == {}


def test_token_lines_are_parsed_to_integer_ids(tmp_path):
    """Verifies each two-column token line maps its symbol to the integer in the second column."""
    tokens_path = tmp_path / "tokens.txt"
    tokens_path.write_text("_ 0\nSP 1\na 12\n", encoding="utf-8")
    assert load_token_ids(tokens_path) == {"_": 0, "SP": 1, "a": 12}


def test_surrounding_whitespace_in_token_lines_is_ignored(tmp_path):
    """Verifies leading, trailing and tab separators around token columns are ignored."""
    tokens_path = tmp_path / "tokens.txt"
    tokens_path.write_text("  padded \t 9  \n", encoding="utf-8")
    assert load_token_ids(tokens_path) == {"padded": 9}


def test_token_lines_without_exactly_two_columns_are_skipped(tmp_path):
    """Verifies token lines with one or three or more columns never reach the table."""
    tokens_path = tmp_path / "tokens.txt"
    tokens_path.write_text("lonely\nextra 1 2\nkept 7\n", encoding="utf-8")
    assert load_token_ids(tokens_path) == {"kept": 7}


def test_blank_token_lines_are_skipped(tmp_path):
    """Verifies blank and whitespace-only token lines are ignored."""
    tokens_path = tmp_path / "tokens.txt"
    tokens_path.write_text("\n   \nkept 3\n\n", encoding="utf-8")
    assert load_token_ids(tokens_path) == {"kept": 3}


def test_missing_lexicon_file_gives_an_empty_lexicon(tmp_path):
    """Verifies a missing lexicon.txt yields an empty lexicon instead of an error."""
    assert load_lexicon(tmp_path / "lexicon.txt") == {}


def test_lexicon_line_keeps_the_phonemes_and_drops_the_tones(tmp_path):
    """Verifies the first half of the columns after the word are kept as phonemes."""
    lexicon_path = tmp_path / "lexicon.txt"
    lexicon_path.write_text("mundo m u n d o 0 0 0 0 0\n", encoding="utf-8")
    assert load_lexicon(lexicon_path) == {"mundo": ["m", "u", "n", "d", "o"]}


def test_lexicon_words_are_lower_cased(tmp_path):
    """Verifies the lexicon key is lower-cased while the phonemes are kept as written."""
    lexicon_path = tmp_path / "lexicon.txt"
    lexicon_path.write_text("Casa k a s a 0 0 0 0\n", encoding="utf-8")
    assert load_lexicon(lexicon_path) == {"casa": ["k", "a", "s", "a"]}


def test_lexicon_word_with_one_phoneme_and_one_tone_is_kept(tmp_path):
    """Verifies the shortest valid lexicon line, one phoneme followed by one tone, is kept."""
    lexicon_path = tmp_path / "lexicon.txt"
    lexicon_path.write_text("pair k 0\n", encoding="utf-8")
    assert load_lexicon(lexicon_path) == {"pair": ["k"]}


def test_lexicon_line_with_an_odd_number_of_columns_after_the_word_is_skipped(
    tmp_path,
):
    """Verifies a lexicon line with an odd count after the word is skipped and parsing goes on."""
    lexicon_path = tmp_path / "lexicon.txt"
    lexicon_path.write_text("odd k a s 0 0\nkept k 0\n", encoding="utf-8")
    assert load_lexicon(lexicon_path) == {"kept": ["k"]}


def test_lexicon_line_with_only_a_word_and_one_column_is_skipped(tmp_path):
    """Verifies a lexicon line holding a word and a single column is skipped."""
    lexicon_path = tmp_path / "lexicon.txt"
    lexicon_path.write_text("lone k\n", encoding="utf-8")
    assert load_lexicon(lexicon_path) == {}


def test_lexicon_lines_with_fewer_than_two_columns_and_blanks_are_skipped(tmp_path):
    """Verifies a bare word and blank or whitespace-only lexicon lines are skipped."""
    lexicon_path = tmp_path / "lexicon.txt"
    lexicon_path.write_text("\n   \nlone\n", encoding="utf-8")
    assert load_lexicon(lexicon_path) == {}


def test_accented_lexicon_word_loads_as_utf8(tmp_path):
    """Verifies a lexicon word with an accent is read as UTF-8 and kept whole."""
    lexicon_path = tmp_path / "lexicon.txt"
    lexicon_path.write_text(
        "atención a t e n s j o n 0 0 0 0 0 0 0 0\n", encoding="utf-8"
    )
    assert load_lexicon(lexicon_path) == {
        "atención": ["a", "t", "e", "n", "s", "j", "o", "n"]
    }
