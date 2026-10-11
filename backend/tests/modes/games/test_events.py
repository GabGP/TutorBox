"""Validation matrix of the game event a phone reports (modes/games/events.py)."""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from modes.games.events import GameEvent


def make_event(**overrides) -> dict:
    event = {
        "client_event_id": "evt-0000000000000001",
        "grade": "primero",
        "lesson_id": "sumar-jocotes",
        "round_index": 0,
        "attempt": 1,
        "is_correct": False,
        "answer": "4",
        "expected": "5",
        "occurred_at": "2026-10-09T15:04:05Z",
        "app_version": "1",
    }
    event.update(overrides)
    return event


def without(field: str) -> dict:
    event = make_event()
    del event[field]
    return event


INVALID_EVENTS = [
    pytest.param(without("client_event_id"), id="missing-client-event-id"),
    pytest.param(
        make_event(client_event_id="evt 0000000000000001"), id="id-with-a-space"
    ),
    pytest.param(make_event(grade="Primero"), id="uppercase-grade"),
    pytest.param(make_event(grade=""), id="empty-grade"),
    pytest.param(make_event(lesson_id="Sumar Jocotes"), id="lesson-with-space"),
    pytest.param(make_event(round_index=-1), id="negative-round"),
    pytest.param(make_event(round_index=1000), id="round-above-999"),
    pytest.param(make_event(attempt=0), id="attempt-zero"),
    pytest.param(make_event(attempt=100), id="attempt-above-99"),
    pytest.param(make_event(is_correct="yes"), id="is-correct-as-text"),
    pytest.param(make_event(is_correct=1), id="is-correct-as-number"),
    pytest.param(without("is_correct"), id="missing-is-correct"),
    pytest.param(
        make_event(occurred_at="2026-10-09T15:04:05"), id="timestamp-without-zone"
    ),
    pytest.param(make_event(occurred_at="ayer"), id="timestamp-not-a-date"),
    pytest.param(without("occurred_at"), id="missing-occurred-at"),
    pytest.param(
        make_event(occurred_at="0001-01-01T00:00:00+14:00"),
        id="timestamp-out-of-range-in-utc",
    ),
    pytest.param(make_event(answer="x" * 65), id="answer-of-65-characters"),
    pytest.param(make_event(expected="x" * 65), id="expected-of-65-characters"),
    pytest.param(make_event(app_version="x" * 17), id="app-version-of-17-characters"),
]


def test_a_valid_event_parses_and_keeps_its_values():
    event = GameEvent.model_validate(make_event())

    assert event.client_event_id == "evt-0000000000000001"
    assert (event.grade, event.lesson_id) == ("primero", "sumar-jocotes")
    assert (event.round_index, event.attempt, event.is_correct) == (0, 1, False)
    assert (event.answer, event.expected, event.app_version) == ("4", "5", "1")
    assert event.occurred_at == datetime(2026, 10, 9, 15, 4, 5, tzinfo=timezone.utc)


def test_an_offset_timestamp_is_converted_to_utc():
    event = GameEvent.model_validate(
        make_event(occurred_at="2026-10-09T09:04:05-06:00")
    )

    assert event.occurred_at == datetime(2026, 10, 9, 15, 4, 5, tzinfo=timezone.utc)
    assert event.occurred_at.utcoffset() == timedelta(0)


def test_optional_fields_may_be_missing_and_are_none():
    event_without_optional_fields = make_event()
    for field in ("answer", "expected", "app_version"):
        del event_without_optional_fields[field]

    event = GameEvent.model_validate(event_without_optional_fields)

    assert (event.answer, event.expected, event.app_version) == (None, None, None)


def test_unknown_extra_fields_are_ignored():
    event = GameEvent.model_validate(make_event(phone_model="Pixel 7"))

    assert not hasattr(event, "phone_model")


def test_an_unknown_grade_and_lesson_are_valid():
    event = GameEvent.model_validate(make_event(grade="cuarto", lesson_id="nueva"))

    assert (event.grade, event.lesson_id) == ("cuarto", "nueva")


@pytest.mark.parametrize("length", [16, 64])
def test_a_client_event_id_of_16_to_64_characters_is_valid(length):
    event = GameEvent.model_validate(make_event(client_event_id="a" * length))

    assert event.client_event_id == "a" * length


@pytest.mark.parametrize("length", [15, 65])
def test_a_client_event_id_outside_16_to_64_characters_is_invalid(length):
    with pytest.raises(ValidationError):
        GameEvent.model_validate(make_event(client_event_id="a" * length))


@pytest.mark.parametrize("event", INVALID_EVENTS)
def test_a_malformed_event_is_rejected(event):
    with pytest.raises(ValidationError):
        GameEvent.model_validate(event)


@pytest.mark.parametrize("raw_event", ["texto", 7, None, []])
def test_a_value_that_is_not_an_object_is_rejected(raw_event):
    with pytest.raises(ValidationError):
        GameEvent.model_validate(raw_event)
