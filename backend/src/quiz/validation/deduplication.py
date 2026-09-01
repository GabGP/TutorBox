"""Deterministic deduplication validator rejecting duplicate quiz questions against seed bank."""

import re
import unicodedata
from collections.abc import Sequence
from difflib import SequenceMatcher

from pydantic import BaseModel, Field

from math_engine.equation_parser import parse_equation_components
from math_engine.parser import are_values_equivalent
from quiz.contracts.models import QuizQuestionBase
from quiz.seed_data import SEED_QUESTIONS

_REPL = {"÷": "/", "×": "*", "·": "*"}
_LATEX_REPL = {r"\cdot": "*", r"\times": "*", r"\div": "/"}


class DeduplicationValidationResult(BaseModel):
    """Result of question deduplication validation against reference questions."""

    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    similarity_score: float = 0.0
    matched_question_text: str | None = None


def normalize_question_text(text: str) -> str:
    """Normalizes question text for robust deduplication comparison."""
    norm = "".join(
        c
        for c in unicodedata.normalize("NFKD", text.lower())
        if not unicodedata.combining(c)
    )
    for p in ("¿", "?", "¡", "!", ":", ";", ",", "."):
        norm = norm.replace(p, " ")
    for src, tgt in {**_REPL, **_LATEX_REPL}.items():
        norm = norm.replace(src, tgt)
    return re.sub(r"\s+", " ", norm).strip()


def extract_math_core(text: str) -> str | None:
    """Extracts mathematical equation or arithmetic core without framing."""
    norm = normalize_question_text(text)
    if "=" in norm and (
        m := re.search(r"([0-9a-z\s\+\-\*/\(\)\^]+=[0-9a-z\s\+\-\*/\(\)\^]+)", norm)
    ):
        return re.sub(r"\s+", "", m.group(1))
    if arith := re.search(r"[\d\(\)][\d\s\+\-\*/\(\)\.\^%]+[\d\)]", norm):
        return re.sub(r"\s+", "", arith.group(0))
    return None


def calculate_text_similarity(text_a: str, text_b: str) -> float:
    """Computes similarity between two normalized strings."""
    if text_a == text_b:
        return 1.0
    seq_ratio = SequenceMatcher(None, text_a, text_b).ratio()
    tok_a, tok_b = set(text_a.split()), set(text_b.split())
    jaccard = len(tok_a & tok_b) / len(tok_a | tok_b) if (tok_a | tok_b) else 0.0
    return max(seq_ratio, jaccard)


class DeduplicationValidator:
    """Validates candidate questions for novelty against reference seed questions."""

    def __init__(
        self,
        reference_questions: Sequence[QuizQuestionBase] | None = None,
        similarity_threshold: float = 0.90,
    ) -> None:
        self.reference_questions = (
            list(reference_questions)
            if reference_questions is not None
            else SEED_QUESTIONS
        )
        self.similarity_threshold = similarity_threshold

    def _has_identical_math_expression(self, text_a: str, text_b: str) -> bool:
        """Checks if two questions contain identical algebraic equations or arithmetic expressions."""
        eq_a = parse_equation_components(text_a)
        eq_b = parse_equation_components(text_b)
        if eq_a and eq_b:
            left_a, right_a, var_a = eq_a
            left_b, right_b, var_b = eq_b
            l_sub = left_b.subs(var_b, var_a)
            r_sub = right_b.subs(var_b, var_a)
            match_direct = are_values_equivalent(
                left_a, l_sub
            ) and are_values_equivalent(right_a, r_sub)
            match_flipped = are_values_equivalent(
                left_a, r_sub
            ) and are_values_equivalent(right_a, l_sub)
            return match_direct or match_flipped
        core_a, core_b = extract_math_core(text_a), extract_math_core(text_b)
        return bool(core_a and core_b and core_a == core_b)

    @staticmethod
    def _build_error(ref_text: str) -> str:
        return (
            f"Your generated question duplicates an existing question in the bank ('{ref_text}'). "
            "Generate a new question with different numerical values and coefficients."
        )

    def _check_reference_match(
        self,
        question: QuizQuestionBase,
        ref: QuizQuestionBase,
        norm_candidate: str,
    ) -> tuple[bool, float]:
        norm_ref = normalize_question_text(ref.question_text)
        if norm_candidate == norm_ref or self._has_identical_math_expression(
            question.question_text, ref.question_text
        ):
            return True, 1.0
        core_c = extract_math_core(question.question_text)
        core_r = extract_math_core(ref.question_text)
        if core_c is None and core_r is None:
            sim = calculate_text_similarity(norm_candidate, norm_ref)
            return (sim >= self.similarity_threshold, sim)
        return False, 0.0

    def validate_question_novelty(
        self, question: QuizQuestionBase
    ) -> DeduplicationValidationResult:
        """Deterministically checks whether candidate question duplicates any reference question."""
        norm_candidate = normalize_question_text(question.question_text)
        highest_sim, most_similar_ref = 0.0, None

        for ref in self.reference_questions:
            is_dup, sim = self._check_reference_match(question, ref, norm_candidate)
            if sim > highest_sim:
                highest_sim, most_similar_ref = sim, ref
            if is_dup:
                return DeduplicationValidationResult(
                    is_valid=False,
                    errors=[self._build_error(ref.question_text)],
                    similarity_score=sim,
                    matched_question_text=ref.question_text,
                )

        matched_text = most_similar_ref.question_text if most_similar_ref else None
        return DeduplicationValidationResult(
            is_valid=True,
            errors=[],
            similarity_score=highest_sim,
            matched_question_text=matched_text,
        )
