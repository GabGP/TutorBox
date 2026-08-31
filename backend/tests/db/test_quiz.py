"""Unit tests for the quiz questions database repository layer."""

import os
import sqlite3
import tempfile

import pytest

from quiz.models import DistractorDetail, QuizQuestion, QuizQuestionCreate
from src.db.database import get_db_connection
from src.db.migrations import apply_migrations
from src.db.quiz import (
    count_questions,
    create_question,
    get_question_by_id,
    get_random_questions,
    list_questions,
    soft_delete_question,
)


@pytest.fixture
def test_db():
    """Provides an isolated, migrated SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        db_path = tmp_file.name

    apply_migrations(db_path)
    connection = get_db_connection(db_path)

    yield connection

    connection.close()
    if os.path.exists(db_path):
        os.remove(db_path)


def _make_sample_question_create(
    topic: str = "arithmetic_integers",
    subconcept: str = "addition",
    question_text: str = "¿Cuánto es 5 + 3?",
) -> QuizQuestionCreate:
    return QuizQuestionCreate(
        topic=topic,
        subconcept=subconcept,
        question_text=question_text,
        options={"A": "8", "B": "7", "C": "15", "D": "2"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="off_by_one",
                explanation="Restaste 1 en lugar de sumar exactamente.",
            ),
            "C": DistractorDetail(
                misconception="multiplied_instead_of_added",
                explanation="Multiplicaste 5 por 3 en lugar de sumar.",
            ),
            "D": DistractorDetail(
                misconception="subtracted_instead_of_added",
                explanation="Restaste 3 de 5 en lugar de sumar.",
            ),
        },
    )


def test_create_and_get_question_by_id(test_db: sqlite3.Connection):
    question_payload = _make_sample_question_create()
    question_id = create_question(
        test_db, question_payload, source="teacher", sympy_verified=True
    )

    assert question_id.startswith("q_")
    retrieved = get_question_by_id(test_db, question_id)

    assert retrieved is not None
    assert retrieved.id == question_id
    assert retrieved.topic == "arithmetic_integers"
    assert retrieved.subconcept == "addition"
    assert retrieved.question_text == "¿Cuánto es 5 + 3?"
    assert retrieved.options["A"] == "8"
    assert retrieved.correct_option == "A"
    assert retrieved.distractors["B"].misconception == "off_by_one"
    assert retrieved.sympy_verified is True
    assert retrieved.source == "teacher"
    assert retrieved.created_at is not None


def test_create_with_explicit_id(test_db: sqlite3.Connection):
    sample = _make_sample_question_create()
    explicit_question = QuizQuestion(
        id="custom_q_100",
        topic=sample.topic,
        subconcept=sample.subconcept,
        question_text=sample.question_text,
        options=sample.options,
        correct_option=sample.correct_option,
        distractors=sample.distractors,
    )

    created_id = create_question(test_db, explicit_question)
    assert created_id == "custom_q_100"

    retrieved = get_question_by_id(test_db, "custom_q_100")
    assert retrieved is not None
    assert retrieved.id == "custom_q_100"


def test_get_non_existent_question(test_db: sqlite3.Connection):
    assert get_question_by_id(test_db, "non_existent_id") is None


def test_list_questions_with_filters_and_pagination(test_db: sqlite3.Connection):
    create_question(
        test_db,
        _make_sample_question_create(
            topic="arithmetic_integers",
            subconcept="addition",
            question_text="Question number 1?",
        ),
    )
    create_question(
        test_db,
        _make_sample_question_create(
            topic="arithmetic_integers",
            subconcept="multiplication",
            question_text="Question number 2?",
        ),
    )
    create_question(
        test_db,
        _make_sample_question_create(
            topic="fractions",
            subconcept="simplification",
            question_text="Question number 3?",
        ),
    )

    # Filter by topic
    arithmetic_items = list_questions(test_db, topic="arithmetic_integers")
    assert len(arithmetic_items) == 2

    # Filter by topic and subconcept
    addition_items = list_questions(
        test_db, topic="arithmetic_integers", subconcept="addition"
    )
    assert len(addition_items) == 1
    assert addition_items[0].question_text == "Question number 1?"

    # Filter by subconcept only
    subconcept_items = list_questions(test_db, subconcept="simplification")
    assert len(subconcept_items) == 1
    assert subconcept_items[0].question_text == "Question number 3?"

    # Pagination
    paginated_items = list_questions(test_db, limit=2, offset=0)
    assert len(paginated_items) == 2

    offset_items = list_questions(test_db, limit=2, offset=2)
    assert len(offset_items) == 1


def test_get_random_questions(test_db: sqlite3.Connection):
    for index in range(10):
        create_question(
            test_db,
            _make_sample_question_create(
                topic="fractions" if index % 2 == 0 else "pre_algebra",
                subconcept="simplification" if index % 2 == 0 else "inverse_operations",
                question_text=f"Random question number {index}?",
            ),
        )

    random_sample = get_random_questions(
        test_db, topic="fractions", subconcept="simplification", count=3
    )
    assert len(random_sample) == 3
    for item in random_sample:
        assert item.topic == "fractions"
        assert item.subconcept == "simplification"

    # Random without filters
    all_sample = get_random_questions(test_db, count=4)
    assert len(all_sample) == 4


def test_count_questions(test_db: sqlite3.Connection):
    create_question(
        test_db,
        _make_sample_question_create(
            topic="pre_algebra",
            subconcept="linear_equations",
            question_text="Question pre algebra 1?",
        ),
    )
    create_question(
        test_db,
        _make_sample_question_create(
            topic="pre_algebra",
            subconcept="linear_equations",
            question_text="Question pre algebra 2?",
        ),
    )
    create_question(
        test_db,
        _make_sample_question_create(
            topic="fractions",
            subconcept="simplification",
            question_text="Question fractions 3?",
        ),
    )

    assert count_questions(test_db) == 3
    assert count_questions(test_db, topic="pre_algebra") == 2
    assert (
        count_questions(
            test_db,
            topic="pre_algebra",
            subconcept="linear_equations",
        )
        == 2
    )
    assert count_questions(test_db, subconcept="simplification") == 1
    assert count_questions(test_db, topic="non_existent") == 0


def test_soft_delete_question(test_db: sqlite3.Connection):
    question_id = create_question(test_db, _make_sample_question_create())

    assert get_question_by_id(test_db, question_id) is not None
    assert count_questions(test_db) == 1

    # Perform soft delete
    deleted = soft_delete_question(test_db, question_id)
    assert deleted is True

    # Cannot delete already deleted question
    assert soft_delete_question(test_db, question_id) is False

    # Should not appear in standard lookup or counts
    assert get_question_by_id(test_db, question_id) is None
    assert get_question_by_id(test_db, question_id, include_deleted=True) is not None
    assert count_questions(test_db) == 0
    assert count_questions(test_db, include_deleted=True) == 1

    # Should not appear in list_questions unless include_deleted=True
    assert len(list_questions(test_db)) == 0
    assert len(list_questions(test_db, include_deleted=True)) == 1

    # Should not appear in random question sampling
    assert len(get_random_questions(test_db, count=5)) == 0


def test_create_question_invalid_source_raises_integrity_error(
    test_db: sqlite3.Connection,
):
    sample = _make_sample_question_create()
    with pytest.raises(sqlite3.IntegrityError):
        create_question(test_db, sample, source="unsupported_source")
