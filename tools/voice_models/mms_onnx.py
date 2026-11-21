"""Exports a downloaded MMS checkpoint to model.onnx for the classroom voice engine.

The backend runs the Mayan voices with ONNX Runtime, so it never loads PyTorch.
The export needs PyTorch and transformers once, from the mayan-audio extra that
run.py installs. A trace of the full model (random noise included) gives the
same audio as transformers for every input length, checked on 2026-11-20.
"""

import os
import warnings
from pathlib import Path
from typing import Any

from tools.voice_models.catalog import MMS_ONNX_NAME
from tools.voice_models.console import TAG_FAIL, TAG_INFO, TAG_OK

ONNX_OPSET = 17
# Trace input: a realistic length (about one clause), blanks between characters.
TRACE_TOKEN_COUNT = 105


def _trace_token_ids(vocab_size: int) -> list[int]:
    return [
        0 if index % 2 == 0 else 1 + index % (vocab_size - 1)
        for index in range(TRACE_TOKEN_COUNT)
    ]


def _export(model_dir: Path, onnx_path: Path) -> None:
    import torch
    from transformers import VitsModel

    class _WaveformOnly(torch.nn.Module):
        def __init__(self, model: Any) -> None:
            super().__init__()
            self.model = model

        def forward(self, input_ids: Any) -> Any:
            return self.model(input_ids=input_ids).waveform

    model = VitsModel.from_pretrained(str(model_dir)).eval()
    trace_ids = torch.tensor([_trace_token_ids(model.config.vocab_size)])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        torch.onnx.export(
            _WaveformOnly(model),
            (trace_ids,),
            str(onnx_path),
            input_names=["input_ids"],
            output_names=["waveform"],
            dynamic_axes={"input_ids": {1: "tokens"}, "waveform": {1: "samples"}},
            opset_version=ONNX_OPSET,
            dynamo=False,
        )


def export_mms_onnx(model_dir: Path, force: bool = False) -> bool:
    """Writes <model_dir>/model.onnx unless it is already there."""
    onnx_path = model_dir / MMS_ONNX_NAME
    if onnx_path.is_file() and onnx_path.stat().st_size > 0 and not force:
        print(f"{TAG_OK} Already present: {model_dir.name}/{MMS_ONNX_NAME}")
        return True
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except ImportError:
        print(
            f"{TAG_FAIL} Exporting {model_dir.name} needs the mayan-audio packages: "
            "./run.py installs them (uv sync --all-extras)."
        )
        return False

    print(f"{TAG_INFO} Exporting {model_dir.name} to ONNX for the classroom voice...")
    part_path = onnx_path.with_suffix(onnx_path.suffix + ".part")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    try:
        _export(model_dir, part_path)
        os.replace(part_path, onnx_path)
    except Exception as err:  # noqa: BLE001 - any export failure fails the step
        part_path.unlink(missing_ok=True)
        print(f"{TAG_FAIL} ONNX export of {model_dir.name} failed: {err}")
        return False
    print(f"{TAG_OK} Exported: {model_dir.name}/{MMS_ONNX_NAME}")
    return True
