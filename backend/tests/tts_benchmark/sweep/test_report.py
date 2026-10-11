"""Verifies summary column ordering and the summary CSV written for the sweep."""

import csv

import pytest

from tools.benchmark.tts.sweep.report import (
    COLUMNS_ORDER,
    SUMMARY_FILE_NAME,
    get_fieldnames,
    write_summary,
)


def read_summary_rows(summary_file):
    """Reads the summary CSV back as dicts using the csv module's own newline rules."""
    with open(summary_file, newline="", encoding="utf-8") as summary_handle:
        return list(csv.DictReader(summary_handle))


def test_columns_order_lists_the_seventeen_summary_columns():
    """Verifies COLUMNS_ORDER names the seventeen summary columns in the sweep order."""
    assert COLUMNS_ORDER == (
        "engine",
        "provider",
        "cold_first_s",
        "warm_p50_s",
        "warm_p95_s",
        "rtf_p50",
        "peak",
        "load_ms",
        "rss_delta_mb",
        "vram_delta_mb",
        "rss_scope",
        "sr_hz",
        "wav_kb",
        "wav",
        "text_idx",
        "text",
        "error",
    )


def test_summary_file_name_is_summary_csv():
    """Verifies the summary file keeps its fixed name."""
    assert SUMMARY_FILE_NAME == "summary.csv"


def test_no_rows_gives_no_fieldnames():
    """Verifies an empty row list produces an empty column list."""
    assert get_fieldnames([]) == []


def test_known_columns_follow_columns_order_regardless_of_dict_order():
    """Verifies known columns follow COLUMNS_ORDER even when the dict is reversed."""
    rows = [{"error": "", "wav": "a.wav", "provider": "cpu", "engine": "piper"}]
    assert get_fieldnames(rows) == ["engine", "provider", "wav", "error"]


def test_column_present_in_only_one_row_is_included():
    """Verifies a column that only some rows carry still gets a header."""
    rows = [{"engine": "piper"}, {"engine": "espeak", "load_ms": 12.5}]
    assert get_fieldnames(rows) == ["engine", "load_ms"]


def test_unexpected_keys_are_appended_in_sorted_order():
    """Verifies unexpected keys follow the known columns, sorted alphabetically."""
    rows = [{"zeta": 1, "engine": "piper", "alpha": 2}, {"beta": 3}]
    assert get_fieldnames(rows) == ["engine", "alpha", "beta", "zeta"]


def test_write_summary_returns_the_summary_path_inside_output_dir(tmp_path):
    """Verifies write_summary returns output_dir / summary.csv."""
    returned_path = write_summary([{"engine": "piper"}], tmp_path)
    assert returned_path == tmp_path / "summary.csv"
    assert returned_path.is_file()


def test_header_line_joins_the_fieldnames_with_commas(tmp_path):
    """Verifies the first line of the summary is the field names joined by commas."""
    rows = [{"engine": "piper", "warm_p50_s": 1.5, "text": "Hola", "error": ""}]
    summary_file = write_summary(rows, tmp_path)
    header_line = summary_file.read_text(encoding="utf-8").splitlines()[0]
    assert header_line == "engine,warm_p50_s,text,error"


def test_summary_bytes_use_csv_line_endings_and_exact_cells(tmp_path):
    """Verifies the file content matches csv.DictWriter output byte for byte."""
    rows = [
        {"engine": "piper", "warm_p50_s": 1.5, "text": "Hola"},
        {"engine": "espeak", "error": "boom"},
    ]
    summary_file = write_summary(rows, tmp_path)
    assert summary_file.read_bytes().decode("utf-8") == (
        "engine,warm_p50_s,text,error\r\npiper,1.5,Hola,\r\nespeak,,,boom\r\n"
    )


def test_row_missing_some_columns_gets_empty_cells_on_read_back(tmp_path):
    """Verifies columns a row does not carry are read back as empty strings."""
    rows = [
        {"engine": "piper", "warm_p50_s": 1.5},
        {"engine": "espeak", "error": "boom"},
    ]
    summary_file = write_summary(rows, tmp_path)
    assert read_summary_rows(summary_file) == [
        {"engine": "piper", "warm_p50_s": "1.5", "error": ""},
        {"engine": "espeak", "warm_p50_s": "", "error": "boom"},
    ]


def test_non_ascii_text_round_trips_through_utf8(tmp_path):
    """Verifies accented and symbol-rich Spanish text is read back unchanged."""
    rows = [{"engine": "piper", "text": "¿Cuánto es 2 × 3? Atención"}]
    summary_file = write_summary(rows, tmp_path)
    assert read_summary_rows(summary_file) == [
        {"engine": "piper", "text": "¿Cuánto es 2 × 3? Atención"}
    ]


def test_write_summary_does_not_create_a_missing_output_dir(tmp_path):
    """Verifies a missing output directory is not created and makes the write fail."""
    missing_dir = tmp_path / "absent"
    with pytest.raises(FileNotFoundError):
        write_summary([{"engine": "piper"}], missing_dir)
    assert not missing_dir.exists()


def test_write_summary_prints_nothing(tmp_path, capsys):
    """Verifies writing the summary produces no console output."""
    write_summary([{"engine": "piper"}], tmp_path)
    assert capsys.readouterr().out == ""
