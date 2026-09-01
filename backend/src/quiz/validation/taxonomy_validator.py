from pydantic import BaseModel, Field

from quiz.contracts.models import QuizQuestionBase
from quiz.contracts.taxonomy import CURRICULUM_TAXONOMY


class TaxonomyValidationResult(BaseModel):
    is_valid: bool
    errors: list[str] = Field(default_factory=list)


class TaxonomyValidator:
    """Deterministically validates topic, subconcept, and distractor misconception whitelist."""

    def __init__(self, allow_unknown_topics: bool = False) -> None:
        self.allow_unknown_topics = allow_unknown_topics

    def validate_question_taxonomy(
        self,
        question: QuizQuestionBase,
        expected_topic: str,
        expected_subconcept: str | None = None,
    ) -> TaxonomyValidationResult:
        errors: list[str] = []

        if question.topic != expected_topic:
            errors.append(
                f"Topic mismatch: requested '{expected_topic}', "
                f"but generated question has topic '{question.topic}'."
            )

        if expected_subconcept and question.subconcept != expected_subconcept:
            errors.append(
                f"Subconcept mismatch: requested '{expected_subconcept}', "
                f"but generated question has subconcept '{question.subconcept}'."
            )

        if expected_topic in CURRICULUM_TAXONOMY:
            valid_subconcepts = list(CURRICULUM_TAXONOMY[expected_topic].keys())
            if (
                question.subconcept != "general"
                and question.subconcept not in valid_subconcepts
            ):
                errors.append(
                    f"Subconcept '{question.subconcept}' is not recognized under topic "
                    f"'{expected_topic}'. Allowed: {valid_subconcepts}."
                )

            if question.subconcept in CURRICULUM_TAXONOMY[expected_topic]:
                allowed_misconceptions = set(
                    CURRICULUM_TAXONOMY[expected_topic][question.subconcept]
                )
            elif (
                expected_subconcept
                and expected_subconcept in CURRICULUM_TAXONOMY[expected_topic]
            ):
                allowed_misconceptions = set(
                    CURRICULUM_TAXONOMY[expected_topic][expected_subconcept]
                )
            else:
                allowed_misconceptions = {
                    misconception
                    for subconcept_misconceptions in CURRICULUM_TAXONOMY[
                        expected_topic
                    ].values()
                    for misconception in subconcept_misconceptions
                }

            for option_key, distractor in question.distractors.items():
                if distractor.misconception not in allowed_misconceptions:
                    errors.append(
                        f"Misconception '{distractor.misconception}' on option '{option_key}' "
                        f"is invalid for subconcept '{question.subconcept}'. "
                        f"Allowed: {sorted(allowed_misconceptions)}."
                    )
        elif not self.allow_unknown_topics:
            errors.append(
                f"Topic '{expected_topic}' is not recognized in curriculum taxonomy. "
                f"Allowed: {sorted(CURRICULUM_TAXONOMY.keys())}."
            )

        return TaxonomyValidationResult(is_valid=len(errors) == 0, errors=errors)
