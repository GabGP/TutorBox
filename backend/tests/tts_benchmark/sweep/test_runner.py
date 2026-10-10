"""Verifies the sweep runner: WAV files, summary rows, progress lines and engine failure handling."""

import pytest

from tools.benchmark.tts.profiling import backend_bridge
from tools.benchmark.tts.profiling.results import EngineStats, ProfileResult
from tools.benchmark.tts.sweep import runner
from tools.benchmark.tts.sweep.runner import run_sweep


def _stats(engine: str, wav_bytes: bytes, provider: str = "cpu") -> EngineStats:
    """Builds an engine record with one cold run whose summary figures are known exactly."""
    only_run = ProfileResult(
        text="hola",
        latency_seconds=0.5,
        audio_duration_seconds=2.0,
        real_time_factor=0.25,
        sample_rate=22050,
        peak_amplitude=0.5,
        audio_byte_count=2048,
        load_ms=120.5,
        rss_delta_mb=12.5,
        vram_delta_mb=3.25,
        cold=True,
        rss_scope="process-tree",
    )
    return EngineStats(
        engine=engine, runs=(only_run,), wav_bytes=wav_bytes, provider=provider
    )


class FakeProfiler:
    """Records each profile_engine call and answers with a scripted record or a scripted error."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str, int]] = []
        self.outcomes: dict[tuple[str, str], object] = {}

    def __call__(
        self, engine: str, text: str, lang: str = "es", repeats: int = 5
    ) -> EngineStats:
        """Logs the call, then returns or raises the outcome scripted for this pair."""
        self.calls.append((engine, text, lang, repeats))
        outcome = self.outcomes.get((engine, text))
        if outcome is None:
            return _stats(engine, f"{engine}|{text}".encode())
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


@pytest.fixture(autouse=True)
def fake_profiler(monkeypatch):
    """Replaces runner.profile_engine so no test ever reaches the real backend."""
    profiler = FakeProfiler()
    monkeypatch.setattr(runner, "profile_engine", profiler)
    return profiler


@pytest.fixture(autouse=True)
def provider_lookup(monkeypatch):
    """Replaces the provider lookup with one that answers cuda and records each engine asked for."""
    requested_engines: list[str] = []

    def fake_detect_engine_provider(engine: str) -> str:
        """Records the engine and answers cuda."""
        requested_engines.append(engine)
        return "cuda"

    monkeypatch.setattr(
        backend_bridge, "detect_engine_provider", fake_detect_engine_provider
    )
    return requested_engines


def test_profile_error_limits_match_the_sweep_contract():
    """Verifies the error and text snippet limits and the errors that count as unavailable."""
    assert runner.MAX_ERROR_SNIPPET_CHARS == 160
    assert runner.MAX_TEXT_SNIPPET_CHARS == 80
    assert runner.PROFILING_ERRORS == (RuntimeError, OSError, ValueError, ImportError)


def test_each_engine_and_text_gets_one_wav_named_by_engine_language_and_index(
    tmp_path, fake_profiler
):
    """Verifies every engine and text pair writes one WAV named engine_language_index."""
    run_sweep(
        ["piper", "espeak"],
        [(0, "hola"), (2, "adiós")],
        language="es",
        repeats=3,
        wav_dir=tmp_path,
    )
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "espeak_es_0.wav",
        "espeak_es_2.wav",
        "piper_es_0.wav",
        "piper_es_2.wav",
    ]
    assert (tmp_path / "piper_es_2.wav").read_bytes() == "piper|adiós".encode()
    assert (tmp_path / "espeak_es_0.wav").read_bytes() == b"espeak|hola"


def test_row_is_the_summary_plus_wav_text_and_text_index(tmp_path, fake_profiler):
    """Verifies a profiled row holds the summary figures plus wav, text and text_idx."""
    rows = run_sweep(
        ["piper"], [(0, "hola")], language="es", repeats=3, wav_dir=tmp_path
    )
    assert rows == [
        {
            "engine": "piper",
            "provider": "cpu",
            "cold_first_s": 0.5,
            "warm_p50_s": 0.5,
            "warm_p95_s": 0.5,
            "rtf_p50": 0.25,
            "peak": 0.5,
            "sr_hz": 22050,
            "wav_kb": 2.0,
            "load_ms": 120.5,
            "rss_delta_mb": 12.5,
            "vram_delta_mb": 3.25,
            "rss_scope": "process-tree",
            "wav": str(tmp_path / "piper_es_0.wav"),
            "text": "hola",
            "text_idx": 0,
        }
    ]
    assert isinstance(rows[0]["wav"], str)


def test_row_text_is_cut_to_eighty_characters(tmp_path, fake_profiler):
    """Verifies a long corpus line is shortened to its first 80 characters in the row."""
    long_text = "palabra " * 20
    rows = run_sweep(
        ["piper"], [(0, long_text)], language="es", repeats=3, wav_dir=tmp_path
    )
    assert len(long_text) == 160
    assert rows[0]["text"] == "palabra " * 10


def test_progress_line_is_printed_with_the_figures_and_the_wav_path(
    tmp_path, fake_profiler, capsys
):
    """Verifies the progress line for a profiled pair matches the sweep's console format."""
    run_sweep(["piper"], [(0, "hola")], language="es", repeats=3, wav_dir=tmp_path)
    expected_line = (
        "[piper:cpu #0] cold=0.5s warm_p50=0.5s rtf=0.25 peak=0.5 "
        f"rss+12.5MB vram+3.25MB (process-tree) -> {tmp_path / 'piper_es_0.wav'}"
    )
    assert capsys.readouterr().out.splitlines() == [expected_line]


def test_progress_line_shows_the_provider_the_engine_ran_on(
    tmp_path, fake_profiler, capsys
):
    """Verifies the progress line names the execution provider from the engine record."""
    fake_profiler.outcomes[("piper", "hola")] = _stats("piper", b"x", provider="cuda")
    run_sweep(["piper"], [(0, "hola")], language="es", repeats=3, wav_dir=tmp_path)
    assert capsys.readouterr().out.startswith("[piper:cuda #0] cold=0.5s")


def test_rows_come_out_engine_major_with_texts_inside(tmp_path, fake_profiler):
    """Verifies all texts of the first engine come before any text of the next engine."""
    rows = run_sweep(
        ["piper", "espeak"],
        [(0, "uno"), (1, "dos")],
        language="es",
        repeats=3,
        wav_dir=tmp_path,
    )
    assert [(row["engine"], row["text_idx"]) for row in rows] == [
        ("piper", 0),
        ("piper", 1),
        ("espeak", 0),
        ("espeak", 1),
    ]
    assert fake_profiler.calls == [
        ("piper", "uno", "es", 3),
        ("piper", "dos", "es", 3),
        ("espeak", "uno", "es", 3),
        ("espeak", "dos", "es", 3),
    ]


def test_language_and_repeats_are_forwarded_to_profile_engine(tmp_path, fake_profiler):
    """Verifies the language goes to profile_engine as lang and names the WAV, repeats as repeats."""
    run_sweep(["piper"], [(0, "hola")], language="ca", repeats=7, wav_dir=tmp_path)
    assert fake_profiler.calls == [("piper", "hola", "ca", 7)]
    assert (tmp_path / "piper_ca_0.wav").is_file()


@pytest.mark.parametrize("error_type", [RuntimeError, OSError, ValueError, ImportError])
def test_unavailable_engine_prints_a_line_and_writes_an_error_row(
    tmp_path, fake_profiler, provider_lookup, capsys, error_type
):
    """Verifies each expected failure prints one unavailable line and yields a four-key error row."""
    fake_profiler.outcomes[("piper", "hola")] = error_type("boom")
    rows = run_sweep(
        ["piper"], [(0, "hola")], language="es", repeats=3, wav_dir=tmp_path
    )
    assert capsys.readouterr().out == "[piper] unavailable: boom\n"
    assert rows == [
        {"engine": "piper", "provider": "cuda", "text_idx": 0, "error": "boom"}
    ]
    assert list(rows[0]) == ["engine", "provider", "text_idx", "error"]
    assert provider_lookup == ["piper"]
    assert list(tmp_path.iterdir()) == []


def test_error_text_is_cut_to_160_characters_in_the_row_only(
    tmp_path, fake_profiler, capsys
):
    """Verifies the error row keeps 160 characters while the console prints the whole message."""
    message = "ab" * 120
    fake_profiler.outcomes[("piper", "hola")] = RuntimeError(message)
    rows = run_sweep(
        ["piper"], [(0, "hola")], language="es", repeats=3, wav_dir=tmp_path
    )
    assert rows[0]["error"] == message[:160]
    assert capsys.readouterr().out == f"[piper] unavailable: {message}\n"


def test_unavailable_line_is_printed_before_the_provider_is_looked_up(
    monkeypatch, tmp_path, fake_profiler, capsys
):
    """Verifies the unavailable line reaches the console before the provider lookup runs."""
    fake_profiler.outcomes[("piper", "hola")] = RuntimeError("boom")
    printed_before_lookup: list[str] = []

    def lookup_after_printing(engine: str) -> str:
        """Records what was printed so far, then answers cpu."""
        printed_before_lookup.append(capsys.readouterr().out)
        return "cpu"

    monkeypatch.setattr(backend_bridge, "detect_engine_provider", lookup_after_printing)
    run_sweep(["piper"], [(0, "hola")], language="es", repeats=3, wav_dir=tmp_path)
    assert printed_before_lookup == ["[piper] unavailable: boom\n"]


def test_failing_engine_does_not_stop_the_following_engine(tmp_path, fake_profiler):
    """Verifies a missing engine gets an error row and the next engine still runs."""
    fake_profiler.outcomes[("piper", "hola")] = RuntimeError("missing model")
    rows = run_sweep(
        ["piper", "espeak"],
        [(0, "hola")],
        language="es",
        repeats=3,
        wav_dir=tmp_path,
    )
    assert rows[0] == {
        "engine": "piper",
        "provider": "cuda",
        "text_idx": 0,
        "error": "missing model",
    }
    assert rows[1]["engine"] == "espeak"
    assert rows[1]["wav"] == str(tmp_path / "espeak_es_0.wav")
    assert [path.name for path in tmp_path.iterdir()] == ["espeak_es_0.wav"]


def test_other_exception_types_propagate_unchanged(tmp_path, fake_profiler):
    """Verifies an error outside the four expected types is not swallowed."""
    fake_profiler.outcomes[("piper", "hola")] = KeyError("missing")
    with pytest.raises(KeyError):
        run_sweep(["piper"], [(0, "hola")], language="es", repeats=3, wav_dir=tmp_path)


def test_empty_engine_list_gives_no_rows_and_no_profiling(tmp_path, fake_profiler):
    """Verifies an empty engine list returns no rows and never profiles anything."""
    rows = run_sweep([], [(0, "hola")], language="es", repeats=3, wav_dir=tmp_path)
    assert rows == []
    assert fake_profiler.calls == []


def test_empty_text_list_gives_no_rows_and_no_profiling(tmp_path, fake_profiler):
    """Verifies an empty text list returns no rows and never profiles anything."""
    rows = run_sweep(["piper"], [], language="es", repeats=3, wav_dir=tmp_path)
    assert rows == []
    assert fake_profiler.calls == []


def test_run_sweep_does_not_create_the_wav_folder(tmp_path, fake_profiler):
    """Verifies a missing WAV folder makes the write fail; the caller is the one that creates it."""
    wav_dir = tmp_path / "absent"
    with pytest.raises(FileNotFoundError):
        run_sweep(["piper"], [(0, "hola")], language="es", repeats=3, wav_dir=wav_dir)
    assert not wav_dir.exists()
