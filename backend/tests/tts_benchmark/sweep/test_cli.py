"""Verifies the sweep command line: flag parsing, engine validation, corpus handling and the run outcome."""

import csv
import dataclasses
import sys
from pathlib import Path

import pytest

from tools.benchmark.tts.profiling import backend_bridge, engine_run
from tools.benchmark.tts.shared import paths
from tools.benchmark.tts.sweep import cli

SAMPLE_ROW = {"engine": "piper", "provider": "cpu", "text_idx": 0, "text": "hola"}
SUMMARY_COLUMNS = [
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
]


class RunSweepSpy:
    """Records each run_sweep call and returns the rows it was told to return."""

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.rows_to_return: list[dict] = [dict(SAMPLE_ROW)]

    def __call__(self, engines, evaluation_texts, *, language, repeats, wav_dir):
        """Records the forwarded arguments and returns a copy of the canned rows."""
        self.calls.append(
            {
                "engines": engines,
                "evaluation_texts": evaluation_texts,
                "language": language,
                "repeats": repeats,
                "wav_dir": wav_dir,
            }
        )
        return list(self.rows_to_return)


class FakeMemoryMonitor:
    """Stands in for MemoryMonitor with fixed memory readings."""

    rss_delta_mb = 12.5
    vram_delta_mb = 3.25
    scope = "uma-unified"

    def __enter__(self):
        """Starts the monitored block."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Ends the monitored block without suppressing errors."""


@pytest.fixture
def run_sweep_spy(monkeypatch):
    """Replaces cli.run_sweep with a recorder so most tests skip real synthesis."""
    spy = RunSweepSpy()
    monkeypatch.setattr(cli, "run_sweep", spy)
    return spy


def _set_arguments(monkeypatch, *flags: str) -> None:
    """Sets sys.argv to a script name followed by the given flags."""
    monkeypatch.setattr(sys, "argv", ["sweep.py", *flags])


def _run_flags(corpus_path: Path, output_dir: Path, *extra_flags: str) -> list[str]:
    """Returns the corpus and output flags followed by any extra flags."""
    return ["--corpus", str(corpus_path), "--out", str(output_dir), *extra_flags]


def _write_corpus(tmp_path: Path, content: str) -> Path:
    """Writes a corpus file as UTF-8 text and returns its path."""
    corpus_path = tmp_path / "es_math.txt"
    corpus_path.write_text(content, encoding="utf-8")
    return corpus_path


def test_exit_code_and_repeat_constants_have_their_documented_values():
    """Verifies the default repeat count and the three exit codes keep their values."""
    assert cli.DEFAULT_SWEEP_REPEATS == 3
    assert cli.EXIT_SUCCESS == 0
    assert cli.EXIT_EMPTY_CORPUS == 2


def test_defaults_without_flags_sweep_four_engines_three_times_in_spanish(monkeypatch):
    """Verifies a run without flags uses the four default engines, three repeats and the shared paths."""
    _set_arguments(monkeypatch)
    options = cli.parse_arguments()
    assert options.engines == ["qwen3-tts", "sherpa", "piper", "espeak"]
    assert options.repeats == 3
    assert options.corpus_path == paths.DEFAULT_CORPUS_FILE
    assert options.output_dir == paths.DEFAULT_RESULTS_DIR
    assert options.language == "es"
    assert options.all_texts is False


def test_default_paths_are_read_when_the_arguments_are_parsed(monkeypatch, tmp_path):
    """Verifies the default corpus and output paths come from the shared paths at call time."""
    monkeypatch.setattr(paths, "DEFAULT_CORPUS_FILE", tmp_path / "other.txt")
    monkeypatch.setattr(paths, "DEFAULT_RESULTS_DIR", tmp_path / "results")
    _set_arguments(monkeypatch)
    options = cli.parse_arguments()
    assert options.corpus_path == tmp_path / "other.txt"
    assert options.output_dir == tmp_path / "results"


def test_explicit_flags_are_parsed_and_the_qwen_alias_is_resolved(monkeypatch):
    """Verifies every flag is read, the qwen alias becomes qwen3-tts and duplicates drop out."""
    _set_arguments(
        monkeypatch,
        "--engines",
        "Qwen, Piper,piper",
        "--repeats",
        "5",
        "--corpus",
        "corpus.txt",
        "--out",
        "results",
        "--lang",
        "ca",
        "--all-texts",
    )
    options = cli.parse_arguments()
    assert options.engines == ["qwen3-tts", "piper"]
    assert options.repeats == 5
    assert options.corpus_path == Path("corpus.txt")
    assert options.output_dir == Path("results")
    assert options.language == "ca"
    assert options.all_texts is True


def test_unsupported_engine_exits_with_code_two_and_names_it(monkeypatch, capsys):
    """Verifies an unknown engine makes the parser exit with code 2 and name the engine."""
    _set_arguments(monkeypatch, "--engines", "bogus")
    with pytest.raises(SystemExit) as exit_info:
        cli.parse_arguments()
    assert exit_info.value.code == 2
    assert capsys.readouterr().err.endswith(
        "error: unsupported engine(s): bogus; use qwen3-tts for Qwen\n"
    )


def test_empty_engine_list_exits_with_code_two(monkeypatch, capsys):
    """Verifies an empty engine list makes the parser exit with code 2 and say why."""
    _set_arguments(monkeypatch, "--engines", ",")
    with pytest.raises(SystemExit) as exit_info:
        cli.parse_arguments()
    assert exit_info.value.code == 2
    assert capsys.readouterr().err.endswith(
        "error: --engines must contain at least one engine\n"
    )


def test_empty_corpus_prints_a_message_and_creates_no_output_folder(
    monkeypatch, tmp_path, capsys, run_sweep_spy
):
    """Verifies an empty corpus returns 2 before any folder is created or any sweep runs."""
    corpus_path = _write_corpus(tmp_path, "\n   \n\t\n")
    output_dir = tmp_path / "results"
    _set_arguments(monkeypatch, *_run_flags(corpus_path, output_dir))
    assert cli.main() == 2
    captured = capsys.readouterr()
    assert captured.err == "empty corpus\n"
    assert captured.out == ""
    assert not output_dir.exists()
    assert run_sweep_spy.calls == []


def test_normal_run_creates_the_wav_folder_and_writes_the_summary(
    monkeypatch, tmp_path, capsys, run_sweep_spy
):
    """Verifies a normal run passes the first text to the sweep and writes summary.csv."""
    corpus_path = _write_corpus(tmp_path, "hola\nadiós\n")
    output_dir = tmp_path / "results"
    _set_arguments(
        monkeypatch,
        *_run_flags(corpus_path, output_dir, "--engines", "piper", "--repeats", "2"),
    )
    assert cli.main() == 0
    assert (output_dir / "out").is_dir()
    assert run_sweep_spy.calls == [
        {
            "engines": ["piper"],
            "evaluation_texts": [(0, "hola")],
            "language": "es",
            "repeats": 2,
            "wav_dir": output_dir / "out",
        }
    ]
    summary_file = output_dir / "summary.csv"
    assert summary_file.read_bytes().decode("utf-8") == (
        "engine,provider,text_idx,text\r\npiper,cpu,0,hola\r\n"
    )
    captured = capsys.readouterr()
    assert captured.out == f"wrote {summary_file}\n"
    assert captured.err == ""


@pytest.mark.parametrize(
    ("extra_flags", "expected_texts"),
    [
        ([], [(0, "uno")]),
        (["--all-texts"], [(0, "uno"), (1, "dos"), (2, "tres")]),
    ],
    ids=["first-text-only", "all-texts"],
)
def test_text_selection_follows_the_all_texts_flag(
    monkeypatch, tmp_path, run_sweep_spy, extra_flags, expected_texts
):
    """Verifies only the first corpus line is evaluated unless --all-texts asks for every line."""
    corpus_path = _write_corpus(tmp_path, "uno\n\n  dos  \ntres\n")
    _set_arguments(monkeypatch, *_run_flags(corpus_path, tmp_path / "r", *extra_flags))
    cli.main()
    assert run_sweep_spy.calls[0]["evaluation_texts"] == expected_texts


def test_no_rows_prints_a_notice_writes_no_csv_and_still_succeeds(
    monkeypatch, tmp_path, capsys, run_sweep_spy
):
    """Verifies a sweep with no rows prints the notice on stderr, writes no CSV and returns 0."""
    run_sweep_spy.rows_to_return = []
    corpus_path = _write_corpus(tmp_path, "hola\n")
    output_dir = tmp_path / "results"
    _set_arguments(monkeypatch, *_run_flags(corpus_path, output_dir))
    assert cli.main() == 0
    captured = capsys.readouterr()
    assert captured.err == "no rows generated\n"
    assert captured.out == ""
    assert not (output_dir / "summary.csv").exists()
    assert (output_dir / "out").is_dir()


def test_end_to_end_run_writes_the_wav_and_the_csv_for_one_engine(
    monkeypatch, tmp_path, fake_router, capsys
):
    """Verifies a real sweep through the fake router writes the WAV and a one-row summary CSV."""
    monkeypatch.setattr(engine_run, "MemoryMonitor", FakeMemoryMonitor)
    monkeypatch.setattr(backend_bridge, "detect_engine_provider", lambda engine: "cpu")
    corpus_path = _write_corpus(tmp_path, "hola\n")
    output_dir = tmp_path / "results"
    _set_arguments(
        monkeypatch,
        *_run_flags(corpus_path, output_dir, "--engines", "piper", "--repeats", "2"),
    )
    assert cli.main() == 0

    wav_file = output_dir / "out" / "piper_es_0.wav"
    assert wav_file.read_bytes() == fake_router.wav_bytes
    summary_file = output_dir / "summary.csv"
    with open(summary_file, newline="", encoding="utf-8") as summary_handle:
        reader = csv.DictReader(summary_handle)
        assert reader.fieldnames == SUMMARY_COLUMNS
        summary_rows = list(reader)
    assert len(summary_rows) == 1
    assert summary_rows[0]["engine"] == "piper"
    assert summary_rows[0]["provider"] == "cpu"
    assert summary_rows[0]["wav"] == str(wav_file)
    assert summary_rows[0]["text"] == "hola"
    assert summary_rows[0]["text_idx"] == "0"
    assert summary_rows[0]["rss_delta_mb"] == "12.5"
    assert summary_rows[0]["vram_delta_mb"] == "3.25"
    assert summary_rows[0]["rss_scope"] == "uma-unified"

    captured = capsys.readouterr()
    assert captured.out.splitlines()[0].startswith("[piper:cpu #0] cold=")
    assert captured.out.splitlines()[-1] == f"wrote {summary_file}"


def test_sweep_options_are_frozen_after_creation():
    """Verifies the parsed sweep options cannot be changed after they are built."""
    options = cli.SweepOptions(["piper"], 3, Path("c.txt"), Path("r"), "es", False)
    with pytest.raises(dataclasses.FrozenInstanceError):
        options.repeats = 9
