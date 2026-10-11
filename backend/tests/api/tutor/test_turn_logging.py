"""Turn labels: built from a real tutor turn, and stored by the Mode 2 endpoint."""

from fractions import Fraction

import pytest

from api.tutor.gate import TurnGate
from api.tutor.roster import TutorRoster
from api.tutor.service import get_roster, get_turn_gate, get_tutor
from api.tutor.turn_logging import build_turn_record
from core.db.turn_log_repository import TurnRecord
from core.llm import MockLLMClient
from modes.socratic import ConversationStore, SocraticTutor, TurnResult, TutorGateway
from modes.socratic.problems import find_problem
from src.main import app
from tests.conftest import auth_headers

MESSAGE = "/api/v1/tutor/message"
START = (
    "¡Vamos! Queremos resolver 2x + 4 = 14 paso a paso. "
    "¿Qué te pide hacer este problema?"
)
CLUE = (
    "Todavía no. Buscamos el número que falta en 2x + 4 = 14. "
    "¿Qué operación deshace lo que le hicieron a ese número?"
)
STEP = "Todavía no. Primero deshaz el + 4: quita 4 de los dos lados. ¿Cuánto es 14 - 4?"
EXPLANATION = "Una fracción es una parte de un todo, como 1/4. ¿Qué parte comes tú?"
LEAKING = "¡Es 68! ¿Ves?"  # gives away another answer, so the output guard replaces it
# The model's replies, one per model call of the dialogue, in order: the restated
# goal, the concept clue, the first step and the explanation.
DIALOGUE_REPLIES = [START, CLUE, STEP, EXPLANATION]
# (message, (concept_topic, concept_subconcept, cnb_topic, error_type,
#            scaffolding_strategy) as stored in turn_logs)
DIALOGUE = [
    (
        "2x + 4 = 14",
        (
            "pre_algebra",
            "two_step_equations",
            "operaciones_combinadas",
            None,
            "restate_goal",
        ),
    ),
    (
        "10",
        (
            "pre_algebra",
            "two_step_equations",
            "operaciones_combinadas",
            "forgot_division",
            "concept_clue",
        ),
    ),
    (
        "6",
        (
            "pre_algebra",
            "two_step_equations",
            "operaciones_combinadas",
            "unclassified",
            "smaller_step",
        ),
    ),
    (
        "5",
        (
            "pre_algebra",
            "two_step_equations",
            "operaciones_combinadas",
            None,
            "confirm_solution",
        ),
    ),
    (
        "¿qué es una fracción?",
        ("fractions", None, "fracciones", None, "concept_explanation"),
    ),
    ("hola", (None, None, None, None, "social")),
]
TWO_STEP_PROBLEM = find_problem("2x + 4 = 14")


@pytest.fixture
def tutor_mode(client, teacher_headers):
    resp = client.put("/api/v1/mode", json={"mode": "tutor"}, headers=teacher_headers)
    assert resp.status_code == 200


@pytest.fixture
def services():
    """A tutor whose model answers the dialogue, and a gate that lets it through."""
    model = MockLLMClient(DIALOGUE_REPLIES)
    tutor = SocraticTutor(
        TutorGateway(model, max_concurrent=1, queue_seconds=0.1), ConversationStore()
    )
    app.dependency_overrides[get_tutor] = lambda: tutor
    app.dependency_overrides[get_turn_gate] = lambda: TurnGate(turns_per_minute=20)
    app.dependency_overrides[get_roster] = lambda: TutorRoster()
    yield
    app.dependency_overrides.clear()


def _tutor(*replies: str) -> SocraticTutor:
    gateway = TutorGateway(
        MockLLMClient(list(replies)), max_concurrent=1, queue_seconds=0.1
    )
    return SocraticTutor(gateway, ConversationStore())


def _turns(tutor: SocraticTutor, *messages: str) -> list[TurnResult]:
    return [tutor.respond("login-1", message) for message in messages]


def _labels(record: TurnRecord) -> tuple:
    return (
        record.concept_topic,
        record.concept_subconcept,
        record.cnb_topic,
        record.error_type,
        record.scaffolding_strategy,
    )


def _say(client, headers, message):
    return client.post(MESSAGE, json={"message": message}, headers=headers)


def test_a_wrong_answer_is_labelled_with_its_misconception_and_rung():
    _, wrong = _turns(_tutor(START, CLUE), "2x + 4 = 14", "10")

    assert build_turn_record("session-1", "10", wrong) == TurnRecord(
        session_id="session-1",
        user_input="10",
        final_response=CLUE,
        hint_level=1,
        containment_triggered=False,
        expression="2x + 4 = 14",
        target="5",
        is_correct=False,
        llm_raw=CLUE,
        concept_topic="pre_algebra",
        concept_subconcept="two_step_equations",
        cnb_topic="operaciones_combinadas",
        error_type="forgot_division",
        scaffolding_strategy="concept_clue",
    )


def test_a_wrong_answer_no_rule_predicts_is_unclassified():
    _, _, wrong = _turns(_tutor(START, CLUE, STEP), "2x + 4 = 14", "10", "6")

    assert _labels(build_turn_record("session-1", "6", wrong)) == (
        "pre_algebra",
        "two_step_equations",
        "operaciones_combinadas",
        "unclassified",
        "smaller_step",
    )


def test_a_correct_answer_is_confirmed_and_has_no_error_type():
    _, right = _turns(_tutor(START), "2x + 4 = 14", "5")

    record = build_turn_record("session-1", "5", right)

    assert (record.is_correct, record.error_type) == (True, None)
    assert record.scaffolding_strategy == "confirm_solution"


def test_a_concept_question_is_labelled_by_its_cnb_topic_without_a_problem():
    (explained,) = _turns(_tutor(EXPLANATION), "¿qué es una fracción?")

    record = build_turn_record("session-1", "¿qué es una fracción?", explained)

    assert (record.expression, record.target, record.is_correct) == (None, None, None)
    assert _labels(record) == (
        "fractions",
        None,
        "fracciones",
        None,
        "concept_explanation",
    )


def test_a_greeting_has_no_concept_and_no_error_type():
    (greeting,) = _turns(_tutor(), "hola")

    assert _labels(build_turn_record("session-1", "hola", greeting)) == (
        None,
        None,
        None,
        None,
        "social",
    )


@pytest.mark.parametrize(
    ("problem", "attempt"),
    [(TWO_STEP_PROBLEM, None), (None, Fraction(10))],
    ids=["without an attempt", "without a problem"],
)
def test_a_wrong_answer_missing_its_problem_or_attempt_gets_no_error_type(
    problem, attempt
):
    result = TurnResult(
        reply="Todavía no.",
        kind="hint",
        hint_level=1,
        used_model=False,
        containment_triggered=False,
        llm_raw=None,
        problem=problem,
        is_correct=False,
        topic_id=None,
        attempt=attempt,
    )

    assert build_turn_record("session-1", "10", result).error_type is None


def test_the_labels_do_not_depend_on_what_the_model_said():
    leaking = _turns(_tutor(LEAKING, LEAKING), "2x + 4 = 14", "10")
    unreachable = _turns(_tutor(), "2x + 4 = 14", "10")

    assert leaking[1].containment_triggered
    assert [_labels(build_turn_record("s", "x", turn)) for turn in leaking] == [
        _labels(build_turn_record("s", "x", turn)) for turn in unreachable
    ]


def test_the_endpoint_stores_the_labels_of_every_turn(
    staff_db, client, tutor_mode, services
):
    headers = auth_headers(client, "student1")
    for message, _expected in DIALOGUE:
        assert _say(client, headers, message).status_code == 200

    _, conn = staff_db
    rows = conn.execute(
        "SELECT concept_topic, concept_subconcept, cnb_topic, error_type, "
        "scaffolding_strategy FROM turn_logs ORDER BY id"
    ).fetchall()
    assert [tuple(row) for row in rows] == [expected for _, expected in DIALOGUE]
