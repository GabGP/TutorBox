import sqlite3
from pathlib import Path

from db.migrations import apply_migrations
from db.quiz import get_question_by_id, list_questions, soft_delete_question
from quiz.contracts.models import DistractorDetail, QuizQuestion
from quiz.seed_data import SEED_QUESTIONS, seed_question_bank


def test_seed_question_bank_with_connection(temp_db: tuple[str, sqlite3.Connection]):
    """Verifies seeding questions using an active database connection."""
    _, conn = temp_db
    inserted_first = seed_question_bank(conn)
    assert inserted_first == len(SEED_QUESTIONS)

    all_questions = list_questions(conn, limit=100)
    assert len(all_questions) == len(SEED_QUESTIONS)

    first_question = get_question_by_id(conn, SEED_QUESTIONS[0].id)
    assert first_question is not None
    assert first_question.source == "seed"
    assert first_question.sympy_verified is True

    # Idempotent re-run
    inserted_second = seed_question_bank(conn)
    assert inserted_second == 0


def test_seed_question_bank_with_db_path(tmp_path: Path):
    """Verifies seeding questions using a filesystem database path string."""
    db_file = tmp_path / "test_seed.db"
    db_path_str = str(db_file)

    apply_migrations(db_path_str)
    inserted = seed_question_bank(db_path_str)
    assert inserted == len(SEED_QUESTIONS)

    # Re-run idempotency
    inserted_again = seed_question_bank(db_path_str)
    assert inserted_again == 0


def test_seed_question_bank_custom_subset(temp_db: tuple[str, sqlite3.Connection]):
    """Verifies seeding a specific custom subset of questions."""
    _, conn = temp_db
    custom_question = QuizQuestion(
        id="custom_seed_01",
        topic="arithmetic",
        subconcept="addition_subtraction",
        question_text="¿Cuánto es 10 + 10?",
        options={"A": "20", "B": "10", "C": "0", "D": "100"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="borrowing_error",
                explanation="Ignoraste el segundo término.",
            ),
            "C": DistractorDetail(
                misconception="added_instead_of_subtracted",
                explanation="Restaste en vez de sumar.",
            ),
            "D": DistractorDetail(
                misconception="sign_error",
                explanation="Multiplicaste en vez de sumar.",
            ),
        },
    )

    inserted = seed_question_bank(conn, questions=[custom_question])
    assert inserted == 1

    stored = get_question_by_id(conn, "custom_seed_01")
    assert stored is not None
    assert stored.id == "custom_seed_01"


def test_seed_question_bank_ignores_soft_deleted(
    temp_db: tuple[str, sqlite3.Connection],
):
    """Verifies seeder does not recreate questions that were soft-deleted."""
    _, conn = temp_db
    custom_question = QuizQuestion(
        id="deleted_seed_01",
        topic="arithmetic",
        subconcept="addition_subtraction",
        question_text="¿Cuánto es 5 + 5?",
        options={"A": "10", "B": "5", "C": "0", "D": "25"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="borrowing_error",
                explanation="Copia.",
            ),
            "C": DistractorDetail(
                misconception="added_instead_of_subtracted",
                explanation="Resta.",
            ),
            "D": DistractorDetail(
                misconception="sign_error",
                explanation="Multiplica.",
            ),
        },
    )

    seed_question_bank(conn, questions=[custom_question])
    soft_delete_question(conn, "deleted_seed_01")

    assert get_question_by_id(conn, "deleted_seed_01", include_deleted=False) is None

    re_seed_count = seed_question_bank(conn, questions=[custom_question])
    assert re_seed_count == 0
