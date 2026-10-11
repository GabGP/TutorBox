"""Tutor turn telemetry in turn_logs (core/db/turn_log_repository.py)."""

from core.db.turn_log_repository import TurnRecord, record_turn
from tests.conftest import get_user_id


def test_record_turn_stores_every_column(seeded_db):
    _, conn = seeded_db
    user_id = get_user_id(conn, "student1")
    conn.execute("INSERT INTO sessions (id, user_id) VALUES ('login-1', ?)", (user_id,))

    record_turn(
        conn,
        TurnRecord(
            session_id="login-1",
            user_input="23 + 45",
            final_response="¿Por dónde empiezas?",
            hint_level=0,
            containment_triggered=True,
            expression="23 + 45",
            target="68",
            llm_raw="<think>…</think>Es 68",
        ),
    )
    record_turn(
        conn, TurnRecord("login-1", "68", "¡Muy bien!", 1, False, is_correct=True)
    )
    conn.commit()

    rows = conn.execute(
        "SELECT user_input, sympy_evaluated_expression, sympy_target_result, "
        "sympy_is_correct, llm_raw_response, containment_triggered, final_response, "
        "hint_level FROM turn_logs ORDER BY id"
    ).fetchall()
    assert [tuple(row) for row in rows] == [
        (
            "23 + 45",
            "23 + 45",
            "68",
            None,
            "<think>…</think>Es 68",
            1,
            "¿Por dónde empiezas?",
            0,
        ),
        ("68", None, None, 1, None, 0, "¡Muy bien!", 1),
    ]


def test_record_turn_stores_pedagogy_labels_when_given(seeded_db):
    _, conn = seeded_db
    user_id = get_user_id(conn, "student1")
    conn.execute("INSERT INTO sessions (id, user_id) VALUES ('login-1', ?)", (user_id,))

    record_turn(
        conn,
        TurnRecord(
            session_id="login-1",
            user_input="3/4 + 1/4",
            final_response="¿Qué pasa con los denominadores?",
            hint_level=1,
            containment_triggered=False,
            is_correct=False,
            concept_topic="fractions",
            concept_subconcept="addition_subtraction",
            cnb_topic="fracciones",
            error_type="added_denominators",
            scaffolding_strategy="concept_clue",
        ),
    )
    conn.commit()

    row = conn.execute(
        "SELECT concept_topic, concept_subconcept, cnb_topic, error_type, "
        "scaffolding_strategy FROM turn_logs"
    ).fetchone()
    assert tuple(row) == (
        "fractions",
        "addition_subtraction",
        "fracciones",
        "added_denominators",
        "concept_clue",
    )


def test_record_turn_leaves_pedagogy_labels_null_when_omitted(seeded_db):
    _, conn = seeded_db
    user_id = get_user_id(conn, "student1")
    conn.execute("INSERT INTO sessions (id, user_id) VALUES ('login-1', ?)", (user_id,))

    record_turn(conn, TurnRecord("login-1", "hola", "¡Hola!", 0, False))
    conn.commit()

    row = conn.execute(
        "SELECT concept_topic, concept_subconcept, cnb_topic, error_type, "
        "scaffolding_strategy FROM turn_logs"
    ).fetchone()
    assert tuple(row) == (None, None, None, None, None)
