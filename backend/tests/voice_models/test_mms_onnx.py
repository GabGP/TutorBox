"""Unit tests for the MMS ONNX export step (tools/voice_models/mms_onnx.py)."""

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from tools.voice_models import mms_onnx


def _fake_export_libraries(write_onnx=True, error=None):
    """Fake torch and transformers modules; torch.onnx.export writes the file."""
    fake_torch = MagicMock()
    fake_torch.nn.Module = object

    def export(_module, _args, path, **kwargs):
        if error:
            raise error
        if write_onnx:
            with open(path, "wb") as onnx_file:
                onnx_file.write(b"onnx")
        fake_torch.export_kwargs = kwargs

    fake_torch.onnx.export.side_effect = export
    fake_transformers = MagicMock()
    model = MagicMock()
    model.config = SimpleNamespace(vocab_size=37)
    fake_transformers.VitsModel.from_pretrained.return_value.eval.return_value = model
    return (
        patch.dict(
            sys.modules, {"torch": fake_torch, "transformers": fake_transformers}
        ),
        fake_torch,
        fake_transformers,
    )


def test_trace_ids_put_a_blank_between_characters():
    trace_ids = mms_onnx._trace_token_ids(37)
    assert len(trace_ids) == mms_onnx.TRACE_TOKEN_COUNT
    assert trace_ids[0::2] == [0] * len(trace_ids[0::2])
    assert all(1 <= token < 37 for token in trace_ids[1::2])


def _fake_onnxruntime(input_names=("input_ids", "speaking_rate"), error=None):
    fake = MagicMock()
    if error:
        fake.InferenceSession.side_effect = error
    fake.InferenceSession.return_value.get_inputs.return_value = [
        SimpleNamespace(name=name) for name in input_names
    ]
    return patch.dict(sys.modules, {"onnxruntime": fake})


def test_current_export_is_kept(tmp_path, capsys):
    (tmp_path / "model.onnx").write_bytes(b"onnx")
    with _fake_onnxruntime():
        assert mms_onnx.export_mms_onnx(tmp_path) is True
    assert "Already present" in capsys.readouterr().out


def test_export_without_the_speaking_rate_input_is_redone(tmp_path):
    """A model.onnx from before the speaking_rate input is exported again."""
    (tmp_path / "model.onnx").write_bytes(b"old")
    libraries, _, _ = _fake_export_libraries()
    with _fake_onnxruntime(input_names=("input_ids",)), libraries:
        assert mms_onnx.export_mms_onnx(tmp_path) is True
    assert (tmp_path / "model.onnx").read_bytes() == b"onnx"


def test_unreadable_export_is_redone(tmp_path):
    (tmp_path / "model.onnx").write_bytes(b"broken")
    libraries, _, _ = _fake_export_libraries()
    with _fake_onnxruntime(error=RuntimeError("bad protobuf")), libraries:
        assert mms_onnx.export_mms_onnx(tmp_path) is True
    assert (tmp_path / "model.onnx").read_bytes() == b"onnx"


def test_export_writes_model_onnx_atomically(tmp_path):
    libraries, fake_torch, fake_transformers = _fake_export_libraries()
    with libraries:
        assert mms_onnx.export_mms_onnx(tmp_path, force=True) is True
    assert (tmp_path / "model.onnx").read_bytes() == b"onnx"
    assert not (tmp_path / "model.onnx.part").exists()
    fake_transformers.VitsModel.from_pretrained.assert_called_once_with(str(tmp_path))
    assert fake_torch.export_kwargs["input_names"] == ["input_ids", "speaking_rate"]
    assert fake_torch.export_kwargs["dynamic_axes"]["input_ids"] == {1: "tokens"}
    assert fake_torch.export_kwargs["opset_version"] == mms_onnx.ONNX_OPSET


def test_export_wrapper_returns_only_the_waveform(tmp_path):
    libraries, fake_torch, _ = _fake_export_libraries()
    with libraries:
        mms_onnx.export_mms_onnx(tmp_path, force=True)
    wrapper = fake_torch.onnx.export.call_args.args[0]
    wrapper.model = MagicMock()
    wrapper.model.return_value.waveform = "waveform"
    assert wrapper.forward("ids", "rate") == "waveform"
    wrapper.model.assert_called_once_with(input_ids="ids", speaking_rate="rate")


def test_export_failure_removes_the_part_file(tmp_path, capsys):
    libraries, _, _ = _fake_export_libraries(error=RuntimeError("trace broke"))
    with libraries:
        assert mms_onnx.export_mms_onnx(tmp_path) is False
    assert not (tmp_path / "model.onnx").exists()
    assert not (tmp_path / "model.onnx.part").exists()
    assert "ONNX export of" in capsys.readouterr().out


def test_export_without_the_mayan_audio_packages(tmp_path, capsys):
    with patch.dict(sys.modules, {"torch": None}):
        assert mms_onnx.export_mms_onnx(tmp_path) is False
    assert "mayan-audio packages" in capsys.readouterr().out
