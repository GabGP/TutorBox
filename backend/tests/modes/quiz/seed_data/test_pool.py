"""Offline checker for the authored question pool (seed_data/pool/*.json).

Runs the same validators the SLM generation loop applies, so a pool file that
passes here can be wired into the seed bank unchanged. Authoring rules are in
docs/quiz/question-pool-brief.md.
"""

import json
import re
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from modes.quiz.contracts.models import QuizQuestion
from modes.quiz.seed_data import SEED_QUESTIONS
from modes.quiz.validation import (
    DistractorConsistencyValidator,
    SymPyMathValidator,
    TaxonomyValidator,
)
from modes.quiz.validation.similarity_helpers import (
    extract_math_core,
    normalize_question_text,
)

POOL_DIR = (
    Path(__file__).resolve().parents[4]
    / "src"
    / "modes"
    / "quiz"
    / "seed_data"
    / "pool"
)

PoolEntry = tuple[str, str, str, dict[str, Any]]  # (topic, subconcept, label, raw)


def _load_pool(pool_dir: Path) -> list[PoolEntry]:
    """Reads every <topic>__<subconcept>.json array; label falls back to file#index."""
    entries: list[PoolEntry] = []
    for pool_file in sorted(pool_dir.glob("*.json")):
        topic, _, subconcept = pool_file.stem.partition("__")
        for index, raw in enumerate(json.loads(pool_file.read_text(encoding="utf-8"))):
            label = raw.get("id") if isinstance(raw, dict) else None
            entries.append(
                (topic, subconcept, label or f"{pool_file.name}#{index}", raw)
            )
    return entries


def _validate_entry(topic: str, subconcept: str, raw: dict[str, Any]) -> list[str]:
    """Applies schema, SymPy, taxonomy and distractor checks; returns all error strings."""
    try:
        question = QuizQuestion.model_validate(raw)
    except ValidationError as exc:
        return [f"schema: {err['msg']}" for err in exc.errors()]

    errors = SymPyMathValidator().validate_question_math(question).errors
    errors += (
        TaxonomyValidator()
        .validate_question_taxonomy(
            question, expected_topic=topic, expected_subconcept=subconcept
        )
        .errors
    )
    errors += (
        DistractorConsistencyValidator()
        .validate_distractor_consistency(question)
        .errors
    )

    slugs = {detail.misconception for detail in question.distractors.values()}
    if len(slugs) != 3:
        errors.append(
            f"Distractors must use 3 different misconception slugs; got {sorted(slugs)}"
        )
    return errors


def _dedup_key(question_text: str) -> str:
    """Same text after normalization, or the same bare expression, counts as a duplicate."""
    return extract_math_core(question_text) or normalize_question_text(question_text)


@pytest.fixture(scope="module")
def pool_entries() -> list[PoolEntry]:
    entries = _load_pool(POOL_DIR) if POOL_DIR.is_dir() else []
    if not entries:
        pytest.skip(f"No pool files under {POOL_DIR}")
    return entries


def test_every_pool_question_passes_all_validators(pool_entries: list[PoolEntry]):
    failures = {
        label: errors
        for topic, subconcept, label, raw in pool_entries
        if (errors := _validate_entry(topic, subconcept, raw))
    }
    report = "\n".join(f"{label}: {errors}" for label, errors in failures.items())
    assert not failures, (
        f"{len(failures)} pool question(s) failed validation:\n{report}"
    )


def test_pool_ids_are_unique_and_follow_convention(pool_entries: list[PoolEntry]):
    ids = [label for _, _, label, _ in pool_entries]
    repeated = sorted({i for i in ids if ids.count(i) > 1})
    assert not repeated, f"Duplicate ids: {repeated}"

    misnamed = [
        label
        for topic, subconcept, label, _ in pool_entries
        if not re.fullmatch(rf"pool_{topic}_{subconcept}_\d{{3}}", label)
    ]
    assert not misnamed, f"Ids must be pool_<topic>_<subconcept>_NNN: {misnamed}"


def test_pool_questions_are_unique_and_not_in_seed_bank(pool_entries: list[PoolEntry]):
    seed_keys = {_dedup_key(seed.question_text): seed.id for seed in SEED_QUESTIONS}
    seen: dict[str, str] = {}
    duplicates: list[str] = []
    for _, _, label, raw in pool_entries:
        key = _dedup_key(str(raw.get("question_text", "")))
        if key in seed_keys:
            duplicates.append(f"{label} repeats seed {seed_keys[key]}")
        elif key in seen:
            duplicates.append(f"{label} repeats {seen[key]}")
        seen.setdefault(key, label)
    assert not duplicates, "\n".join(duplicates)


# --- self-check: the checker must accept a known-good entry and flag a known-bad one

GOOD_ENTRY = {
    "id": "pool_pre_algebra_two_step_equations_001",
    "schema_version": "1.0.0",
    "topic": "pre_algebra",
    "subconcept": "two_step_equations",
    "question_text": "¿Cuál es el valor de x en: 6*x + 9 = 39?",
    "options": {"A": "30", "B": "5", "C": "6", "D": "8"},
    "correct_option": "B",
    "distractors": {
        "A": {
            "misconception": "forgot_division",
            "explanation": "Restaste 9 pero olvidaste dividir entre 6.",
        },
        "C": {
            "misconception": "subtracted_instead_of_divided",
            "explanation": "Restaste 6 en lugar de dividir entre 6 al final.",
        },
        "D": {
            "misconception": "sign_inversion_error",
            "explanation": "Sumaste 9 en lugar de restarlo antes de dividir.",
        },
    },
}

BAD_ENTRY = {
    **GOOD_ENTRY,
    "id": "pool_pre_algebra_two_step_equations_002",
    "options": {"A": "30", "B": "5", "C": "10/2", "D": "1"},
    "distractors": {
        "A": GOOD_ENTRY["distractors"]["A"],
        "C": {
            "misconception": "sign_error",
            "explanation": "Cada 3 unidades cuentan como una.",
        },
        "D": {
            "misconception": "divided_before_subtracting",
            "explanation": "Dividiste 39 / 6 = 6.5 y restaste 9 sin dividir el 9 entre 6.",
        },
    },
}


def test_checker_accepts_good_entry_and_flags_bad_entry(tmp_path: Path):
    pool_file = tmp_path / "pre_algebra__two_step_equations.json"
    pool_file.write_text(json.dumps([GOOD_ENTRY, BAD_ENTRY]), encoding="utf-8")

    results = {
        label: _validate_entry(topic, subconcept, raw)
        for topic, subconcept, label, raw in _load_pool(tmp_path)
    }

    assert results[GOOD_ENTRY["id"]] == []
    bad_errors = "\n".join(results[BAD_ENTRY["id"]])
    assert "Duplicate option values: 'B' and 'C' both equal '5'" in bad_errors
    assert "Distractor 'C' ('10/2') equals the correct solution '5'" in bad_errors
    assert "Misconception 'sign_error' on option 'C' is invalid" in bad_errors
    assert "claims result '3', which contradicts option value '10/2'" in bad_errors
    assert "claims result '6.5', which contradicts option value '1'" in bad_errors


def test_checker_reports_schema_errors_without_crashing(tmp_path: Path):
    broken = {**GOOD_ENTRY, "distractors": {"A": GOOD_ENTRY["distractors"]["A"]}}
    nameless = {k: v for k, v in GOOD_ENTRY.items() if k != "id"}
    pool_file = tmp_path / "pre_algebra__two_step_equations.json"
    pool_file.write_text(json.dumps([broken, nameless]), encoding="utf-8")

    entries = _load_pool(tmp_path)
    assert [label for _, _, label, _ in entries] == [
        GOOD_ENTRY["id"],
        "pre_algebra__two_step_equations.json#1",
    ]
    topic, subconcept, _, raw = entries[0]
    errors = _validate_entry(topic, subconcept, raw)
    assert any("Distractors must match non-correct options" in e for e in errors)
