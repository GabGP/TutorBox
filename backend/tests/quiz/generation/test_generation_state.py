from quiz.generation.generation_state import GenerationState
from quiz.generation.types import GenerationError


def test_generation_state_initialization():
    state = GenerationState(
        model_name="test-slm",
        base_user_prompt="base prompt",
        current_user_prompt="base prompt",
        max_retries=3,
    )
    assert state.model_name == "test-slm"
    assert state.attempt == 1
    assert state.max_retries == 3
    assert state.accumulated_errors == []
    assert state.duration_ms >= 0.0


def test_generation_state_record_rejection():
    state = GenerationState(
        model_name="test-slm",
        base_user_prompt="base prompt",
        current_user_prompt="base prompt",
        max_retries=3,
    )
    state.record_rejection(["Error A", "Error B"], "new feedback prompt")
    assert state.attempt == 2
    assert state.accumulated_errors == ["Error A", "Error B"]
    assert state.current_user_prompt == "new feedback prompt"


def test_generation_state_build_metadata():
    state = GenerationState(
        model_name="test-slm",
        base_user_prompt="base prompt",
        current_user_prompt="base prompt",
        max_retries=3,
    )
    state.record_rejection(["Error A"], "new feedback prompt")
    metadata = state.build_metadata()
    assert metadata.model_name == "test-slm"
    assert metadata.attempts == 2
    assert metadata.rejection_history == ["Error A"]
    assert metadata.duration_ms >= 0.0


def test_generation_state_build_exhaustion_error():
    state = GenerationState(
        model_name="test-slm",
        base_user_prompt="base prompt",
        current_user_prompt="base prompt",
        max_retries=3,
    )
    state.record_rejection(["Err 1", "Err 2"], "prompt 2")
    err = state.build_exhaustion_error()
    assert isinstance(err, GenerationError)
    assert err.attempts == 3
    assert "Failed to generate a valid quiz question after 3 attempts" in str(err)
    assert "Err 1; Err 2" in str(err)
    assert err.model_name == "test-slm"
    assert err.accumulated_errors == ["Err 1", "Err 2"]


def test_generation_state_build_exhaustion_error_empty():
    state = GenerationState(
        model_name="test-slm",
        base_user_prompt="base prompt",
        current_user_prompt="base prompt",
        max_retries=1,
    )
    err = state.build_exhaustion_error()
    assert "No specific validation errors recorded" in str(err)


def test_generation_state_build_llm_failure_error():
    state = GenerationState(
        model_name="test-slm",
        base_user_prompt="base prompt",
        current_user_prompt="base prompt",
        max_retries=3,
    )
    cause = ConnectionError("llama-server unavailable")
    err = state.build_llm_failure_error(cause)
    assert isinstance(err, GenerationError)
    assert err.attempts == 1
    assert "SLM completion request failed on attempt 1" in str(err)
    assert "llama-server unavailable" in str(err)
