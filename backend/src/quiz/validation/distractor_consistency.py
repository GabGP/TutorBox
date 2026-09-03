"""Deterministic validation of distractor explanation consistency and value alignment."""

from typing import Any

from pydantic import BaseModel, Field

from math_engine.parser import are_values_equivalent, parse_option_expression
from quiz.contracts.models import QuizQuestionBase
from quiz.validation.distractor_patterns import (
    INVALID_CLAIM_PATTERNS,
    MIN_EXPLANATION_LENGTH,
    RESULT_CLAIM_PATTERNS,
)


class DistractorConsistencyResult(BaseModel):
    """Result of distractor-to-explanation consistency validation."""

    is_valid: bool
    errors: list[str] = Field(default_factory=list)


class DistractorConsistencyValidator:
    """Validates that distractor explanations match assigned option values without contradictions."""

    def _extract_claimed_results(self, explanation: str) -> list[str]:
        """Extracts candidate numerical outcomes claimed in a Spanish explanation."""
        claims: list[str] = []
        for pattern in RESULT_CLAIM_PATTERNS:
            for match in pattern.finditer(explanation):
                val = match.group(1).strip()
                if val and val not in claims:
                    claims.append(val)
        return claims

    def _check_distractor(
        self,
        option_key: str,
        option_value: str,
        explanation: str,
        misconception: str,
    ) -> list[str]:
        """Checks a single distractor for text length, valid phrasing, and numerical consistency."""
        errors: list[str] = []
        cleaned_explanation = explanation.strip()

        if len(cleaned_explanation) < MIN_EXPLANATION_LENGTH:
            errors.append(
                f"Distractor '{option_key}' explanation is too short "
                f"({len(cleaned_explanation)} chars). Minimum is {MIN_EXPLANATION_LENGTH}."
            )
            return errors

        for invalid_pattern in INVALID_CLAIM_PATTERNS:
            if invalid_pattern.search(cleaned_explanation):
                errors.append(
                    f"Distractor '{option_key}' explanation incorrectly claims this wrong "
                    "option is the correct answer or uses empty boilerplate referencing option letters."
                )

        parsed_option = parse_option_expression(option_value)
        claimed_results = self._extract_claimed_results(cleaned_explanation)

        if claimed_results and parsed_option is not None:
            parsed_claims: list[Any] = [
                parse_option_expression(claim) for claim in claimed_results
            ]
            has_matching_claim = any(
                claim_expr is not None
                and are_values_equivalent(claim_expr, parsed_option)
                for claim_expr in parsed_claims
            )
            if not has_matching_claim:
                first_claim = claimed_results[0]
                errors.append(
                    f"Distractor '{option_key}' explanation claims result '{first_claim}', "
                    f"which contradicts option value '{option_value}'."
                )

        return errors

    def validate_distractor_consistency(
        self, question: QuizQuestionBase
    ) -> DistractorConsistencyResult:
        """Validates all non-correct distractors for internal explanation-to-option consistency."""
        errors: list[str] = []

        for option_key, distractor in question.distractors.items():
            if option_key == question.correct_option:
                continue

            option_value = question.options.get(option_key, "")
            distractor_errors = self._check_distractor(
                option_key=option_key,
                option_value=option_value,
                explanation=distractor.explanation,
                misconception=distractor.misconception,
            )
            errors.extend(distractor_errors)

        return DistractorConsistencyResult(is_valid=len(errors) == 0, errors=errors)
