import json
from unittest.mock import MagicMock, patch

import pytest

from src.quiz.generation.llm_client import LLMClient, LocalSLMClient, MockLLMClient


def test_mock_llm_client_basic_flow():
    client = MockLLMClient(["response 1", "response 2"])
    assert client.generate("sys", "user 1") == "response 1"
    assert client.generate("sys", "user 2") == "response 2"
    # Stays on last response if exhausted
    assert client.generate("sys", "user 3") == "response 2"
    assert len(client.call_history) == 3
    assert client.call_history[0] == ("sys", "user 1")


def test_abstract_llm_client_generate():
    class DummyClient(LLMClient):
        def generate(self, system_prompt: str, user_prompt: str) -> str:
            return super().generate(system_prompt, user_prompt)

    dummy = DummyClient()
    assert dummy.generate("a", "b") is None


def test_mock_llm_client_add_response():
    client = MockLLMClient()
    with pytest.raises(RuntimeError, match="no configured responses"):
        client.generate("sys", "user")

    client.add_response("dynamic response")
    assert client.generate("sys", "user") == "dynamic response"


def test_local_slm_client_initialization():
    client = LocalSLMClient(
        base_url="http://192.168.1.50:8080/v1/",
        model="qwen-2.5",
        timeout_seconds=15.0,
    )
    assert client.base_url == "http://192.168.1.50:8080/v1"
    assert client.model == "qwen-2.5"
    assert client.timeout == 15.0


def test_local_slm_client_successful_request():
    client = LocalSLMClient()
    fake_response_data = {"choices": [{"message": {"content": '{"test": "ok"}'}}]}
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(fake_response_data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        res = client.generate("sys_prompt", "user_prompt")
        assert res == '{"test": "ok"}'
        mock_urlopen.assert_called_once()


def test_local_slm_client_failure_raises_runtime_error():
    client = LocalSLMClient()
    with (
        patch("urllib.request.urlopen", side_effect=Exception("Connection refused")),
        pytest.raises(RuntimeError, match="LocalSLM request failed"),
    ):
        client.generate("sys_prompt", "user_prompt")
