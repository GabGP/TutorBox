"""The misconception a game names for a wrong answer (modes/games/events.py, ingest.py)."""

import pytest
from pydantic import ValidationError

from modes.games.events import GameEvent
from modes.games.ingest import ACCEPTED, REJECTED, ingest_events
from tests.modes.games.test_ingest import INSTALL_ID, _row_for, make_event

EVENT_ID = "evt-0000000000000001"


def test_an_event_without_a_misconception_is_valid():
    event = GameEvent.model_validate(make_event())

    assert event.misconception is None


@pytest.mark.parametrize(
    "slug", ["borrowing_error", "added_instead_of_subtracted", "ab", "a" + "9" * 63]
)
def test_a_snake_case_slug_of_2_to_64_characters_is_valid(slug):
    event = GameEvent.model_validate(make_event(misconception=slug))

    assert event.misconception == slug


@pytest.mark.parametrize(
    "slug",
    [
        "",
        "a",
        "a" * 65,
        "Borrowing_Error",
        "borrowing-error",
        "borrowing error",
        "9_lives",
        "_hidden",
        "resta_mañana",
        7,
        ["borrowing_error"],
    ],
)
def test_a_misconception_that_is_not_a_snake_case_slug_is_invalid(slug):
    with pytest.raises(ValidationError):
        GameEvent.model_validate(make_event(misconception=slug))


def test_the_misconception_of_a_wrong_answer_is_stored(seeded_db):
    _, conn = seeded_db

    statuses = ingest_events(
        conn, INSTALL_ID, None, [make_event(misconception="borrowing_error")]
    )

    assert statuses == [ACCEPTED]
    assert _row_for(conn, EVENT_ID)["misconception"] == "borrowing_error"


def test_a_slug_outside_the_quiz_taxonomy_is_stored_as_sent(seeded_db):
    _, conn = seeded_db

    ingest_events(
        conn, INSTALL_ID, None, [make_event(misconception="residuo_mayor_que_divisor")]
    )

    assert _row_for(conn, EVENT_ID)["misconception"] == "residuo_mayor_que_divisor"


def test_a_wrong_answer_without_a_misconception_stores_null(seeded_db):
    _, conn = seeded_db

    ingest_events(conn, INSTALL_ID, None, [make_event()])

    assert _row_for(conn, EVENT_ID)["misconception"] is None


def test_a_right_answer_never_stores_a_misconception(seeded_db):
    _, conn = seeded_db

    statuses = ingest_events(
        conn,
        INSTALL_ID,
        None,
        [make_event(is_correct=True, answer="5", misconception="borrowing_error")],
    )

    assert statuses == [ACCEPTED]
    assert _row_for(conn, EVENT_ID)["misconception"] is None


def test_a_malformed_misconception_rejects_that_event_alone(seeded_db):
    _, conn = seeded_db

    statuses = ingest_events(
        conn,
        INSTALL_ID,
        None,
        [
            make_event(misconception="Not A Slug"),
            make_event(client_event_id="evt-0000000000000002"),
        ],
    )

    assert statuses == [REJECTED, ACCEPTED]
    assert _row_for(conn, EVENT_ID) is None
