import io
import json
import urllib.error
from email.message import Message
from unittest.mock import MagicMock, patch

import pytest

from llm.client import LocalSLMClient


def test_local_slm_client_initialization_explicit_parameters():
    client = LocalSLMClient(
        base_url="http://192.168.1.50:8080/v1/",
        model="qwen-2.5",
        temperature=0.8,
        timeout_seconds=15.0,
    )
    assert client.base_url == "http://192.168.1.50:8080/v1"
    assert client.model == "qwen-2.5"
    assert client.temperature == 0.8
    assert client.timeout == 15.0


def test_local_slm_client_successful_request():
    client = LocalSLMClient(temperature=0.75)
    fake_response_data = {"choices": [{"message": {"content": '{"test": "ok"}'}}]}
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(fake_response_data).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = None

    with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
        result = client.generate("system_prompt", "user_prompt")
        assert result == '{"test": "ok"}'
        mock_urlopen.assert_called_once()
        request_argument = mock_urlopen.call_args[0][0]
        payload = json.loads(request_argument.data.decode("utf-8"))
        assert payload["temperature"] == 0.75
        assert payload["messages"][0]["content"] == "system_prompt"
        assert payload["messages"][1]["content"] == "user_prompt"


def test_local_slm_client_failure_raises_runtime_error():
    client = LocalSLMClient()
    with (
        patch("urllib.request.urlopen", side_effect=Exception("Connection refused")),
        pytest.raises(RuntimeError, match="LocalSLM request failed"),
    ):
        client.generate("system_prompt", "user_prompt")


def test_local_slm_client_http_error_extracts_body():
    client = LocalSLMClient()
    fake_fp = io.BytesIO(b'{"error": "model not found"}')
    http_error = urllib.error.HTTPError(
        url="http://127.0.0.1:8080/v1/chat/completions",
        code=400,
        msg="Bad Request",
        hdrs=Message(),
        fp=fake_fp,
    )

    with (
        patch("urllib.request.urlopen", side_effect=http_error),
        pytest.raises(
            RuntimeError, match="LocalSLM HTTP 400 \\(Bad Request\\):.*model not found"
        ),
    ):
        client.generate("system_prompt", "user_prompt")


def test_local_slm_client_reads_env_vars(monkeypatch):
    monkeypatch.setenv("SLM_BASE_URL", "http://10.0.0.99:11434/v1")
    monkeypatch.setenv("SLM_MODEL_NAME", "qwen2.5:3b")
    monkeypatch.setenv("SLM_TEMPERATURE", "0.65")
    monkeypatch.setenv("SLM_TIMEOUT_SECONDS", "45.0")
    client = LocalSLMClient()
    assert client.base_url == "http://10.0.0.99:11434/v1"
    assert client.model == "qwen2.5:3b"
    assert client.temperature == 0.65
    assert client.timeout == 45.0


def test_local_slm_client_reads_slm_timeout_alias(monkeypatch):
    monkeypatch.delenv("SLM_TIMEOUT_SECONDS", raising=False)
    monkeypatch.setenv("SLM_TIMEOUT", "90.5")
    client = LocalSLMClient()
    assert client.timeout == 90.5


def test_local_slm_client_invalid_env_temp_and_timeout_fallback(monkeypatch):
    monkeypatch.setenv("SLM_TEMPERATURE", "not_a_valid_float")
    monkeypatch.setenv("SLM_TIMEOUT_SECONDS", "not_a_float")
    client = LocalSLMClient()
    assert client.temperature == 0.7
    assert client.timeout == 60.0


@pytest.mark.parametrize(
    "malformed_response, error_match",
    [
        ({}, "missing 'choices' list"),
        ({"choices": []}, "missing 'choices' list"),
        ({"choices": ["not_a_dict"]}, "choice entry is not an object"),
        ({"choices": [{}]}, "missing 'message.content'"),
        ({"choices": [{"message": {}}]}, "missing 'message.content'"),
    ],
)
def test_local_slm_client_malformed_response_payload(malformed_response, error_match):
    client = LocalSLMClient()
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(malformed_response).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = None

    with (
        patch("urllib.request.urlopen", return_value=mock_response),
        pytest.raises(TypeError, match=error_match),
    ):
        client.generate("system_prompt", "user_prompt")
