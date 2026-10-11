"""Counts of stored game events (core/db/game_event_summary.py)."""

from dataclasses import replace

from core.db.game_event_repository import GameEventRecord, insert_game_event
from core.db.game_event_summary import (
    MAX_LESSONS_IN_SUMMARY,
    GameEventSummary,
    LessonEventCount,
    summarize_game_events,
)

FIRST_PHONE = "install-000000000001"
SECOND_PHONE = "install-000000000002"

SUMAR_JOCOTES = GameEventRecord(
    client_event_id="replaced-per-row",
    install_id=FIRST_PHONE,
    grade="primero",
    lesson_id="sumar-jocotes",
    round_index=0,
    attempt=1,
    is_correct=True,
    occurred_at="2026-10-09 15:04:05",
    cnb_topic="suma_resta",
    concept_topic="arithmetic",
    concept_subconcept="addition_subtraction",
)
ARRIBA_ABAJO = replace(
    SUMAR_JOCOTES,
    lesson_id="arriba-abajo",
    cnb_topic="ubicacion",
    concept_topic=None,
    concept_subconcept=None,
)


def store(conn, *records: GameEventRecord) -> None:
    """Stores the records, giving each one its own client event id."""
    for number, record in enumerate(records):
        insert_game_event(conn, replace(record, client_event_id=f"evt-{number:016d}"))
    conn.commit()


def test_an_empty_table_counts_zero_everywhere(temp_db):
    _, conn = temp_db

    assert summarize_game_events(conn) == GameEventSummary(
        events=0, wrong_events=0, installs=0, lessons=[]
    )


def test_events_wrong_events_and_installs_are_counted(temp_db):
    _, conn = temp_db
    store(
        conn,
        SUMAR_JOCOTES,
        replace(SUMAR_JOCOTES, is_correct=False),
        replace(SUMAR_JOCOTES, is_correct=False, install_id=SECOND_PHONE),
    )

    summary = summarize_game_events(conn)

    assert (summary.events, summary.wrong_events, summary.installs) == (3, 2, 2)


def test_each_lesson_comes_with_its_labels_and_counts(temp_db):
    _, conn = temp_db
    store(conn, SUMAR_JOCOTES, replace(SUMAR_JOCOTES, is_correct=False), ARRIBA_ABAJO)

    summary = summarize_game_events(conn)

    assert summary.lessons == [
        LessonEventCount(
            grade="primero",
            lesson_id="sumar-jocotes",
            cnb_topic="suma_resta",
            concept_topic="arithmetic",
            concept_subconcept="addition_subtraction",
            events=2,
            wrong_events=1,
        ),
        LessonEventCount(
            grade="primero",
            lesson_id="arriba-abajo",
            cnb_topic="ubicacion",
            concept_topic=None,
            concept_subconcept=None,
            events=1,
            wrong_events=0,
        ),
    ]


def test_the_same_lesson_id_in_two_grades_is_two_lessons(temp_db):
    _, conn = temp_db
    fracciones = replace(SUMAR_JOCOTES, lesson_id="fracciones", grade="segundo")
    store(conn, fracciones, replace(fracciones, grade="tercero"))

    lessons = summarize_game_events(conn).lessons

    assert [(lesson.grade, lesson.events) for lesson in lessons] == [
        ("segundo", 1),
        ("tercero", 1),
    ]


def test_lessons_with_the_most_wrong_answers_come_first(temp_db):
    _, conn = temp_db
    store(
        conn,
        SUMAR_JOCOTES,
        SUMAR_JOCOTES,
        SUMAR_JOCOTES,
        replace(ARRIBA_ABAJO, is_correct=False),
    )

    lessons = summarize_game_events(conn).lessons

    assert [lesson.lesson_id for lesson in lessons] == ["arriba-abajo", "sumar-jocotes"]


def test_an_install_id_counts_only_that_phone(temp_db):
    _, conn = temp_db
    store(
        conn,
        replace(SUMAR_JOCOTES, is_correct=False),
        replace(SUMAR_JOCOTES, install_id=SECOND_PHONE),
        replace(ARRIBA_ABAJO, install_id=SECOND_PHONE),
    )

    summary = summarize_game_events(conn, install_id=SECOND_PHONE)

    assert (summary.events, summary.wrong_events, summary.installs) == (2, 0, 1)
    assert sorted(lesson.lesson_id for lesson in summary.lessons) == [
        "arriba-abajo",
        "sumar-jocotes",
    ]


def test_an_install_id_that_sent_nothing_counts_zero(temp_db):
    _, conn = temp_db
    store(conn, SUMAR_JOCOTES)

    summary = summarize_game_events(conn, install_id="install-that-sent-nothing")

    assert summary == GameEventSummary(events=0, wrong_events=0, installs=0, lessons=[])


def test_the_lesson_list_is_capped(temp_db):
    _, conn = temp_db
    invented_lessons = [
        replace(SUMAR_JOCOTES, lesson_id=f"leccion-{number}")
        for number in range(MAX_LESSONS_IN_SUMMARY + 5)
    ]
    store(conn, *invented_lessons)

    summary = summarize_game_events(conn)

    assert summary.events == MAX_LESSONS_IN_SUMMARY + 5
    assert len(summary.lessons) == MAX_LESSONS_IN_SUMMARY
