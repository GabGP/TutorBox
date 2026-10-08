"""A tutor turn end to end with a mock model (engine, gateway, state, prompts)."""

import threading

from core.config.tutor_settings import TutorConfig
from core.llm import LLMClient, MockLLMClient
from modes.socratic import (
    Conversation,
    ConversationStore,
    SocraticTutor,
    TutorGateway,
    TutorSLMClient,
)
from modes.socratic.engine import EXPLAIN_FOLLOW_UP
from modes.socratic.hints import hint
from modes.socratic.problems import find_problem
from modes.socratic.prompts import explain_prompt, rewrite_prompt


def _tutor(*responses: str) -> tuple[SocraticTutor, MockLLMClient]:
    client = MockLLMClient(list(responses))
    gateway = TutorGateway(client, max_concurrent=1, queue_seconds=0.1)
    return SocraticTutor(gateway, ConversationStore()), client


def test_a_safe_model_rewording_is_shown():
    tutor, client = _tutor(
        "<think>...</think>¡Vamos! Queremos juntar 23 y 45. ¿Por dónde empiezas tú?"
    )

    result = tutor.respond("login-1", "¿cuánto es 23 + 45?")

    assert result.reply == "¡Vamos! Queremos juntar 23 y 45. ¿Por dónde empiezas tú?"
    assert result.used_model and not result.containment_triggered
    assert (result.kind, result.hint_level, result.problem.text) == (
        "hint",
        0,
        "23 + 45",
    )
    assert result.llm_raw.startswith("<think>")
    assert "Reescribe este mensaje" in client.call_history[0][1]


def test_a_leaking_model_reply_is_replaced_by_the_deterministic_hint():
    tutor, _ = _tutor("¡Es 68! ¿Ves?")

    result = tutor.respond("login-1", "23 + 45")

    assert result.containment_triggered and not result.used_model
    assert result.reply == hint(find_problem("23 + 45"), 0)
    assert result.llm_raw == "¡Es 68! ¿Ves?"


def test_an_explanation_mid_problem_may_not_leak_that_problems_answer():
    tutor, _ = _tutor(
        "¡Vamos! Queremos juntar 23 y 45. ¿Por dónde empiezas tú?",
        "Un número es una cantidad, como 68. ¿Qué número ves tú?",
    )
    tutor.respond("login-1", "23 + 45")

    result = tutor.respond("login-1", "¿qué es un número?")

    assert result.kind == "explain"
    assert result.containment_triggered and "68" not in result.reply


def test_an_unreachable_model_falls_back_without_containment():
    tutor, _ = _tutor()  # no responses: the mock raises like a dead server

    result = tutor.respond("login-1", "7 por 8")

    assert not result.used_model and not result.containment_triggered
    assert result.llm_raw is None


def test_concept_questions_use_the_explain_prompt_and_replies_skip_the_model():
    tutor, client = _tutor(
        "Una fracción es una parte de un todo, como 1/4. ¿Qué parte comes tú?"
    )

    result = tutor.respond("login-1", "¿qué es una fracción?")
    assert result.used_model and result.topic_id == "fracciones"
    assert "Pregunta del niño" in client.call_history[0][1]

    assert tutor.respond("login-1", "hola").kind == "social"
    assert len(client.call_history) == 1


def test_an_explanation_always_ends_with_a_question_for_the_child():
    tutor, _ = _tutor("Una fracción es una parte de un todo, como 1/4.")

    result = tutor.respond("login-1", "¿qué es una fracción?")

    assert result.reply == (
        f"Una fracción es una parte de un todo, como 1/4. {EXPLAIN_FOLLOW_UP}"
    )


def test_state_is_kept_per_login_and_reset_forgets_it():
    tutor, _ = _tutor("x")

    tutor.respond("a", "23 + 45")
    assert tutor.respond("a", "68").is_correct is True

    tutor.respond("b", "23 + 45")
    tutor.reset("b")
    assert tutor.respond("b", "68").kind == "orphan"


def test_the_turn_result_carries_the_value_the_child_typed():
    tutor, _ = _tutor("x")
    tutor.respond("a", "23 + 45")

    assert tutor.respond("a", "70").attempt == 70
    assert tutor.respond("a", "68").attempt == 68
    assert tutor.respond("b", "7 por 8").attempt is None


class _SlowClient(LLMClient):
    """Holds its slot until released, like a long generation."""

    def __init__(self) -> None:
        self.started = threading.Event()
        self.release = threading.Event()

    def generate(self, system_prompt, user_prompt, response_format=None) -> str:
        self.started.set()
        self.release.wait(5)
        return "ok"


def test_the_gateway_gives_up_when_every_slot_is_busy():
    client = _SlowClient()
    gateway = TutorGateway(client, max_concurrent=1, queue_seconds=0.05)
    worker = threading.Thread(target=gateway.complete, args=("uno",))
    worker.start()
    client.started.wait(5)

    assert gateway.complete("dos") is None

    client.release.set()
    worker.join(5)
    assert gateway.complete("tres") == "ok"


def test_the_tutor_client_sends_one_user_turn_with_a_token_cap():
    config = TutorConfig(model_name="m", max_tokens=99, timeout_seconds=5.0)
    client = TutorSLMClient(config)

    assert client._build_request_payload("", "hola") == {
        "model": "m",
        "messages": [{"role": "user", "content": "hola"}],
        "temperature": 0.6,
        "max_tokens": 99,
    }
    with_system = client._build_request_payload(
        "sys", "hola", response_format={"type": "json_object"}
    )
    assert with_system["messages"][0] == {"role": "system", "content": "sys"}
    assert with_system["response_format"] == {"type": "json_object"}
    assert client.timeout == 5.0


def test_the_store_is_bounded_and_drops_the_least_recent():
    store = ConversationStore(max_entries=2)
    first = Conversation(level=1)
    store.put("a", first)
    store.put("b", Conversation(level=2))

    assert store.get("a") == first  # "a" is now the most recent
    store.put("c", Conversation(level=3))
    assert len(store) == 2
    assert store.get("b") == Conversation()

    store.drop("a")
    store.drop("never-seen")
    assert len(store) == 1


def test_prompts_carry_the_hint_or_the_question():
    assert "«¿cuánto es 3 + 5?»" in rewrite_prompt("¿cuánto es 3 + 5?")
    prompt = explain_prompt("¿qué es?", "fracciones")
    assert "sobre fracciones" in prompt
    assert "«¿qué es?»" in prompt
