import pytest
from llm.mock import MockLLMClient


def test_mock_llm_client_basic_flow():
    client = MockLLMClient(["response 1", "response 2"])
    assert client.generate("system", "user 1") == "response 1"
    assert client.generate("system", "user 2") == "response 2"
    # Exhaustion behavior: repeats last configured response
    assert client.generate("system", "user 3") == "response 2"
    assert len(client.call_history) == 3
    assert client.call_history[0] == ("system", "user 1")
    assert client.call_history[1] == ("system", "user 2")
    assert client.call_history[2] == ("system", "user 3")


def test_mock_llm_client_empty_raises_runtime_error():
    client = MockLLMClient()
    with pytest.raises(RuntimeError, match="MockLLMClient has no configured responses"):
        client.generate("system", "user")


def test_mock_llm_client_add_response_dynamically():
    client = MockLLMClient()
    with pytest.raises(RuntimeError, match="MockLLMClient has no configured responses"):
        client.generate("system", "user")

    client.add_response("dynamically added response")
    assert client.generate("system", "user") == "dynamically added response"
