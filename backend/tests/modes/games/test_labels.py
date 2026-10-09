"""Concept labels of game lessons (modes/games/labels.py)."""

import re
from pathlib import Path

import pytest

from core.config.constants import PROJECT_ROOT
from modes.games.labels import GameLabels, labels_for, load_lesson_topics
from modes.quiz.contracts.taxonomy import is_valid_subconcept, is_valid_topic
from modes.socratic.curriculum import load_curriculum
from modes.socratic.telemetry.concept import Concept, concept_for

GRADE_NUMBERS = {"primero": 1, "segundo": 2, "tercero": 3}
EXPECTED_LESSON_COUNTS = {"primero": 21, "segundo": 26, "tercero": 30}
# segundo and tercero write lesson('id', ...) calls; primero writes objects with
# id, name, emoji, cnb and module fields. The guard test reads both notations.
REGISTRY_LESSON_CALL = re.compile(r"lesson\('([a-z0-9-]+)'")
REGISTRY_LESSON_OBJECT = re.compile(
    r"id:\s*'([a-z0-9-]+)',\s*name:\s*'[^']*',\s*emoji:\s*'[^']*',"
    r"\s*cnb:\s*'[0-9.]+',\s*module:"
)
# (grade, lesson id, CNB topic id) for every lesson in the table.
LESSON_ENTRIES = [
    (grade, lesson_id, cnb_topic)
    for grade, lessons in load_lesson_topics().items()
    for lesson_id, cnb_topic in lessons.items()
]
TAXONOMY_LESSON_KEYS = [
    (grade, lesson_id)
    for grade, lesson_id, _cnb_topic in LESSON_ENTRIES
    if labels_for(grade, lesson_id).concept_topic is not None
]
# A lesson's labels depend only on its CNB topic, so any lesson of a topic will do.
LABELS_BY_CNB_TOPIC = {
    cnb_topic: labels_for(grade, lesson_id)
    for grade, lesson_id, cnb_topic in LESSON_ENTRIES
}


@pytest.mark.parametrize(
    ("grade", "lesson_id", "expected"),
    [
        (
            "primero",
            "sumar-jocotes",
            GameLabels("suma_resta", "arithmetic", "addition_subtraction"),
        ),
        (
            "primero",
            "restar-elotes",
            GameLabels("suma_resta", "arithmetic", "addition_subtraction"),
        ),
        (
            "segundo",
            "multiplicar",
            GameLabels("multiplicacion", "arithmetic", "multiplication_division"),
        ),
        (
            "tercero",
            "division-residuo",
            GameLabels("division", "arithmetic", "multiplication_division"),
        ),
        ("segundo", "fracciones", GameLabels("fracciones", "fractions", None)),
        ("tercero", "fracciones", GameLabels("fracciones", "fractions", None)),
        ("primero", "arriba-abajo", GameLabels("ubicacion", None, None)),
        ("tercero", "seguro-posible", GameLabels("probabilidad", None, None)),
        ("segundo", "cholqij", GameLabels("tiempo", None, None)),
    ],
)
def test_a_lesson_gets_its_cnb_topic_and_its_taxonomy_pair(grade, lesson_id, expected):
    assert labels_for(grade, lesson_id) == expected


def test_a_lesson_id_is_looked_up_within_its_own_grade():
    assert labels_for("segundo", "solidos").cnb_topic == "solidos"
    assert labels_for("primero", "solidos") == GameLabels()


def test_an_unknown_lesson_of_a_known_grade_has_no_labels():
    assert labels_for("segundo", "leccion-que-no-existe") == GameLabels()


def test_an_unknown_grade_has_no_labels():
    assert labels_for("cuarto", "fracciones") == GameLabels()


@pytest.mark.parametrize(("grade", "expected_count"), EXPECTED_LESSON_COUNTS.items())
def test_the_table_holds_the_lesson_count_of_each_grade(grade, expected_count):
    assert len(load_lesson_topics()[grade]) == expected_count


def _registry_path(grade: str) -> Path:
    return (
        PROJECT_ROOT
        / "pwa"
        / "tareas"
        / grade
        / "public"
        / "js"
        / "data"
        / "modules.js"
    )


def _lesson_ids_in_registry(grade: str) -> list[str]:
    text = _registry_path(grade).read_text(encoding="utf-8")
    return REGISTRY_LESSON_CALL.findall(text) + REGISTRY_LESSON_OBJECT.findall(text)


@pytest.mark.parametrize(("grade", "expected_count"), EXPECTED_LESSON_COUNTS.items())
def test_the_table_lists_exactly_the_lessons_the_game_registry_ships(
    grade, expected_count
):
    shipped_lesson_ids = _lesson_ids_in_registry(grade)

    assert len(shipped_lesson_ids) == expected_count
    assert set(shipped_lesson_ids) == set(load_lesson_topics()[grade])


@pytest.mark.parametrize(("grade", "lesson_id", "cnb_topic"), LESSON_ENTRIES)
def test_a_lessons_cnb_topic_is_in_the_curriculum_and_taught_in_its_grade(
    grade, lesson_id, cnb_topic
):
    topic = load_curriculum().get(cnb_topic)

    assert topic is not None
    assert GRADE_NUMBERS[grade] in topic.grades


def test_at_least_one_lesson_is_labelled_with_a_taxonomy_topic():
    assert TAXONOMY_LESSON_KEYS


@pytest.mark.parametrize(("grade", "lesson_id"), TAXONOMY_LESSON_KEYS)
def test_a_lessons_taxonomy_labels_are_in_the_quiz_taxonomy(grade, lesson_id):
    labels = labels_for(grade, lesson_id)

    assert is_valid_topic(labels.concept_topic)
    if labels.concept_subconcept is not None:
        assert is_valid_subconcept(labels.concept_topic, labels.concept_subconcept)


@pytest.mark.parametrize("cnb_topic", sorted(LABELS_BY_CNB_TOPIC))
def test_a_game_cnb_topic_gets_the_same_taxonomy_pair_as_the_tutor(cnb_topic):
    labels = LABELS_BY_CNB_TOPIC[cnb_topic]

    assert concept_for(None, cnb_topic) == Concept(
        labels.concept_topic, labels.concept_subconcept, cnb_topic
    )


def test_the_lesson_table_is_loaded_once_and_then_reused():
    assert load_lesson_topics() is load_lesson_topics()
