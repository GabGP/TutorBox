"""Tests for abstract LLMClient interface."""

import inspect

from llm.base import LLMClient


def test_abstract_llm_client_is_abstract_base_class():
    """Verifies that LLMClient is registered as an abstract base class with required methods."""
    assert inspect.isabstract(LLMClient)
    assert "generate" in LLMClient.__abstractmethods__


def test_abstract_llm_client_generate_super_call():
    """Verifies default abstract generate method behavior via concrete subclass super call."""

    class DummyClient(LLMClient):
        def generate(
            self,
            system_prompt: str,
            user_prompt: str,
            response_format: dict | None = None,
        ) -> str:
            return super().generate(system_prompt, user_prompt, response_format)

    dummy_instance = DummyClient()
    assert dummy_instance.generate("system_prompt", "user_prompt") is None
