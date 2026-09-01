"""Mock LLM client implementation for testing and simulation."""

from llm.base import LLMClient


class MockLLMClient(LLMClient):
    """Mock LLM client for unit tests and local simulation."""

    def __init__(
        self,
        responses: list[str] | None = None,
        *,
        model: str = "mock-model",
    ) -> None:
        self._responses: list[str] = list(responses) if responses else []
        self._index: int = 0
        self.call_history: list[tuple[str, str]] = []
        self.model: str = model

    def add_response(self, response: str) -> None:
        self._responses.append(response)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.call_history.append((system_prompt, user_prompt))
        if not self._responses:
            raise RuntimeError("MockLLMClient has no configured responses.")
        response = self._responses[min(self._index, len(self._responses) - 1)]
        if self._index < len(self._responses) - 1:
            self._index += 1
        return response
