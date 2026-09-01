import pytest
from llm.base import LLMClient


def test_abstract_llm_client_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        LLMClient()


def test_abstract_llm_client_generate_super_call():
    class DummyClient(LLMClient):
        def generate(self, system_prompt: str, user_prompt: str) -> str:
            return super().generate(system_prompt, user_prompt)

    dummy_instance = DummyClient()
    assert dummy_instance.generate("system_prompt", "user_prompt") is None
