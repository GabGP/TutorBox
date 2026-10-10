"""Verifies the MeloTTS harness: paths, support tables, providers, session lifecycle and synthesis inputs."""

import gc
import io
import itertools
import struct
import time
import wave
from pathlib import Path

import numpy as np
import onnxruntime
import pytest

from tools.benchmark.tts.melo.harness import MeloTTSHarness
from tools.benchmark.tts.melo.support_files import load_lexicon, load_token_ids
from tools.benchmark.tts.melo.tokenizer import text_to_token_ids
from tools.benchmark.tts.shared import paths

CUDA_PROVIDERS = ["CUDAExecutionProvider", "CPUExecutionProvider"]
CPU_PROVIDERS = ["CPUExecutionProvider"]
TOKENS_TEXT = "SP 1\np 19\no 18\nr 20\nm 16\nu 23\nn 17\nd 12\n"
LEXICON_TEXT = "mundo m u n d o 0 0 0 0 0\n"
POR_TOKEN_IDS = [0, 19, 0, 18, 0, 20, 0, 1, 0]
MUNDO_TOKEN_IDS = [0, 16, 0, 23, 0, 17, 0, 12, 0, 18, 0, 1, 0]
INPUT_NAMES = [
    "x",
    "x_lengths",
    "tones",
    "sid",
    "noise_scale",
    "length_scale",
    "noise_scale_w",
]


def float32_value(value: float) -> float:
    """Returns value rounded to float32, the precision the model input is stored in."""
    return float(np.float32(value))


class OnnxRecorder:
    """Records each fake InferenceSession the harness builds and each run() call on it."""

    def __init__(self) -> None:
        self.constructions: list[tuple[str, list[str]]] = []
        self.run_calls: list[tuple[object, dict[str, np.ndarray]]] = []
        self.session_output: np.ndarray = np.array(
            [[[0.0, 0.5, -0.5, 1.0]]], dtype=np.float32
        )


@pytest.fixture
def onnx_recorder(monkeypatch) -> OnnxRecorder:
    """Replaces onnxruntime.InferenceSession with a fake that records calls and returns session_output."""
    recorder = OnnxRecorder()

    class FakeInferenceSession:
        """Stands in for onnxruntime.InferenceSession without loading any model."""

        def __init__(self, model_path: str, providers: list[str]) -> None:
            recorder.constructions.append((model_path, providers))

        def run(self, output_names, inputs):
            recorder.run_calls.append((output_names, inputs))
            return [recorder.session_output]

    monkeypatch.setattr(onnxruntime, "InferenceSession", FakeInferenceSession)
    return recorder


@pytest.fixture
def ticking_clock(monkeypatch):
    """Replaces time.perf_counter with a clock that advances by a quarter second per call."""
    clock = itertools.count(start=1.0, step=0.25)
    monkeypatch.setattr(time, "perf_counter", lambda: next(clock))
    return clock


@pytest.fixture
def model_dir(tmp_path: Path) -> Path:
    """Writes a small tokens.txt and lexicon.txt into a model folder and returns it."""
    folder = tmp_path / "melo"
    folder.mkdir()
    (folder / "tokens.txt").write_text(TOKENS_TEXT, encoding="utf-8")
    (folder / "lexicon.txt").write_text(LEXICON_TEXT, encoding="utf-8")
    return folder


def test_default_model_dir_is_the_melo_model_dir_read_at_call_time(
    monkeypatch, tmp_path
):
    """Verifies a harness built without a folder uses paths.MELO_MODEL_DIR as it is at call time."""
    monkeypatch.setattr(paths, "MELO_MODEL_DIR", tmp_path / "redirected")
    assert MeloTTSHarness().model_dir == tmp_path / "redirected"


def test_string_model_dir_is_stored_as_a_path(tmp_path):
    """Verifies a str model folder is converted to a Path."""
    created = MeloTTSHarness(model_dir=str(tmp_path))
    assert isinstance(created.model_dir, Path)
    assert created.model_dir == tmp_path


def test_model_file_paths_sit_inside_the_model_dir(tmp_path):
    """Verifies the model, lexicon and tokens paths are named files in the model folder."""
    created = MeloTTSHarness(model_dir=tmp_path)
    assert created.model_path == tmp_path / "model.onnx"
    assert created.lexicon_path == tmp_path / "lexicon.txt"
    assert created.tokens_path == tmp_path / "tokens.txt"


def test_provider_defaults_to_cpu(tmp_path):
    """Verifies the provider is "cpu" when none is given."""
    assert MeloTTSHarness(model_dir=tmp_path).provider == "cpu"


def test_support_tables_are_read_from_the_model_dir(model_dir):
    """Verifies the tokens and lexicon in the model folder drive the tokenizer."""
    created = MeloTTSHarness(model_dir=model_dir)
    assert created.text_to_token_ids("por") == POR_TOKEN_IDS
    assert created.text_to_token_ids("mundo") == MUNDO_TOKEN_IDS


def test_missing_model_dir_gives_empty_tables_and_tokenizing_still_works(tmp_path):
    """Verifies a folder without support files builds fine and drops every unknown symbol."""
    created = MeloTTSHarness(model_dir=tmp_path / "absent")
    assert created.text_to_token_ids("por") == [0, 0, 0]
    assert created.text_to_token_ids("mundo") == [0, 0, 0]


def test_text_to_token_ids_matches_the_tokenizer_on_the_harness_tables(model_dir):
    """Verifies the method returns what the tokenizer gives for the harness's own tables."""
    created = MeloTTSHarness(model_dir=model_dir)
    expected = text_to_token_ids(
        "Por mundo.",
        load_token_ids(model_dir / "tokens.txt"),
        load_lexicon(model_dir / "lexicon.txt"),
    )
    assert created.text_to_token_ids("Por mundo.") == expected


def test_cuda_provider_asks_for_cuda_with_cpu_as_fallback(
    model_dir, onnx_recorder, ticking_clock
):
    """Verifies provider "cuda" requests the CUDA provider followed by the CPU provider."""
    MeloTTSHarness(model_dir=model_dir, provider="cuda").load()
    assert onnx_recorder.constructions == [
        (str(model_dir / "model.onnx"), CUDA_PROVIDERS)
    ]


def test_cpu_provider_asks_for_the_cpu_provider_only(
    model_dir, onnx_recorder, ticking_clock
):
    """Verifies provider "cpu" requests the CPU provider alone."""
    MeloTTSHarness(model_dir=model_dir, provider="cpu").load()
    assert onnx_recorder.constructions == [
        (str(model_dir / "model.onnx"), CPU_PROVIDERS)
    ]


def test_any_other_provider_name_asks_for_the_cpu_provider_only(
    model_dir, onnx_recorder, ticking_clock
):
    """Verifies a provider name other than "cuda" falls back to the CPU provider alone."""
    MeloTTSHarness(model_dir=model_dir, provider="tpu").load()
    assert onnx_recorder.constructions[0][1] == CPU_PROVIDERS


def test_load_returns_the_clock_difference_in_milliseconds(
    model_dir, onnx_recorder, ticking_clock
):
    """Verifies load() returns the gap between its two clock readings, in milliseconds."""
    assert MeloTTSHarness(model_dir=model_dir).load() == 250.0


def test_load_passes_the_model_path_to_the_session_as_a_string(
    model_dir, onnx_recorder, ticking_clock
):
    """Verifies the session is created from the model path converted to str."""
    MeloTTSHarness(model_dir=model_dir).load()
    model_path_argument = onnx_recorder.constructions[0][0]
    assert isinstance(model_path_argument, str)
    assert model_path_argument == str(model_dir / "model.onnx")


def test_is_loaded_follows_load_and_unload(model_dir, onnx_recorder, ticking_clock):
    """Verifies is_loaded() is False before load, True after it and False after unload."""
    created = MeloTTSHarness(model_dir=model_dir)
    assert created.is_loaded() is False
    created.load()
    assert created.is_loaded() is True
    created.unload()
    assert created.is_loaded() is False


def test_unload_runs_exactly_one_garbage_collection(model_dir, monkeypatch):
    """Verifies unload() calls gc.collect() once."""
    collect_calls: list[str] = []

    def fake_collect() -> int:
        collect_calls.append("collect")
        return 0

    monkeypatch.setattr(gc, "collect", fake_collect)
    MeloTTSHarness(model_dir=model_dir).unload()
    assert collect_calls == ["collect"]


def test_synthesize_loads_the_session_lazily_and_only_once(
    model_dir, onnx_recorder, ticking_clock
):
    """Verifies the first synthesis creates the session and later ones reuse it."""
    created = MeloTTSHarness(model_dir=model_dir)
    assert onnx_recorder.constructions == []
    created.synthesize("por")
    created.synthesize("por")
    assert len(onnx_recorder.constructions) == 1
    assert len(onnx_recorder.run_calls) == 2


def test_text_inputs_are_int64_arrays_holding_the_token_ids(
    model_dir, onnx_recorder, ticking_clock
):
    """Verifies x, x_lengths, tones and sid are int64 arrays with the token values and count."""
    MeloTTSHarness(model_dir=model_dir).synthesize("por")
    output_names, inputs = onnx_recorder.run_calls[0]
    assert output_names is None
    assert list(inputs) == INPUT_NAMES
    assert inputs["x"].dtype == np.int64
    assert inputs["x"].shape == (1, 9)
    assert inputs["x"].tolist() == [POR_TOKEN_IDS]
    assert inputs["x_lengths"].dtype == np.int64
    assert inputs["x_lengths"].shape == (1,)
    assert inputs["x_lengths"].tolist() == [9]
    assert inputs["tones"].dtype == np.int64
    assert inputs["tones"].shape == (1, 9)
    assert inputs["tones"].tolist() == [[0] * 9]
    assert inputs["sid"].dtype == np.int64
    assert inputs["sid"].shape == (1,)
    assert inputs["sid"].tolist() == [0]


def test_scalar_inputs_are_float32_with_the_fixed_model_settings(
    model_dir, onnx_recorder, ticking_clock
):
    """Verifies noise_scale, length_scale and noise_scale_w are float32 at normal speed."""
    MeloTTSHarness(model_dir=model_dir).synthesize("por")
    _, inputs = onnx_recorder.run_calls[0]
    assert inputs["noise_scale"].dtype == np.float32
    assert inputs["noise_scale"].shape == (1,)
    assert inputs["noise_scale"].tolist() == [float32_value(0.667)]
    assert inputs["length_scale"].dtype == np.float32
    assert inputs["length_scale"].shape == (1,)
    assert inputs["length_scale"].tolist() == [1.0]
    assert inputs["noise_scale_w"].dtype == np.float32
    assert inputs["noise_scale_w"].shape == (1,)
    assert inputs["noise_scale_w"].tolist() == [float32_value(0.8)]


def test_double_speed_halves_the_length_scale(model_dir, onnx_recorder, ticking_clock):
    """Verifies speed=2.0 gives a length_scale of 0.5."""
    MeloTTSHarness(model_dir=model_dir).synthesize("por", speed=2.0)
    _, inputs = onnx_recorder.run_calls[0]
    assert inputs["length_scale"].tolist() == [0.5]


def test_speed_below_the_minimum_is_floored_to_point_one(
    model_dir, onnx_recorder, ticking_clock
):
    """Verifies speed=0.0 is floored to 0.1, which gives a length_scale of 10.0."""
    MeloTTSHarness(model_dir=model_dir).synthesize("por", speed=0.0)
    _, inputs = onnx_recorder.run_calls[0]
    assert inputs["length_scale"].tolist() == [10.0]


def test_synthesis_returns_a_44100_hz_mono_16_bit_wav_with_one_frame_per_sample(
    model_dir, onnx_recorder, ticking_clock
):
    """Verifies the squeezed model output becomes a 44.1 kHz mono 16-bit WAV, one frame per sample."""
    onnx_recorder.session_output = np.array([[[0.0, 0.5, -0.5, 1.0]]], dtype=np.float32)
    wav_bytes = MeloTTSHarness(model_dir=model_dir).synthesize("por")
    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        assert wav_file.getframerate() == 44100
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getnframes() == 4
        frames = wav_file.readframes(4)
    assert struct.unpack("<4h", frames) == (0, 16383, -16383, 32767)
