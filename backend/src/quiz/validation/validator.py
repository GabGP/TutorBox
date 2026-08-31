from abc import ABC, abstractmethod

import sympy as sp

from math_engine.parser import (
    are_values_equivalent,
    extract_and_solve_problem,
    parse_option_expression,
)
from quiz.contracts.models import MathValidationResult, QuizQuestion


class MathValidatorInterface(ABC):
    """Abstract interface for quiz math verification (Student B extension point)."""

    @abstractmethod
    def validate_question_math(self, question: QuizQuestion) -> MathValidationResult:
        """Validates mathematical correctness of question and diagnostic distractors."""


class SymPyMathValidator(MathValidatorInterface):
    """Baseline deterministic math validator for arithmetic and linear equations."""

    def _check_duplicates(
        self,
        options: dict[str, str],
        parsed_options: dict[str, sp.Expr | None],
    ) -> list[str]:
        """Detects if two different options share the exact same mathematical or textual value."""
        errors: list[str] = []
        option_keys = list(options.keys())
        for i in range(len(option_keys)):
            for j in range(i + 1, len(option_keys)):
                key_a, key_b = option_keys[i], option_keys[j]
                option_expr_a = parsed_options[key_a]
                option_expr_b = parsed_options[key_b]

                if option_expr_a is not None and option_expr_b is not None:
                    is_duplicate = are_values_equivalent(option_expr_a, option_expr_b)
                else:
                    is_duplicate = (
                        options[key_a].strip().lower() == options[key_b].strip().lower()
                    )

                if is_duplicate:
                    errors.append(
                        f"Duplicate option values: '{key_a}' and '{key_b}' "
                        f"both equal '{options[key_a].strip()}'"
                    )
        return errors

    def validate_question_math(self, question: QuizQuestion) -> MathValidationResult:
        """Validates mathematical correctness of correct answer and distractors."""
        parsed_options = {
            option_key: parse_option_expression(option_text)
            for option_key, option_text in question.options.items()
        }
        errors = self._check_duplicates(question.options, parsed_options)

        expected_solution, eval_mode = extract_and_solve_problem(question.question_text)
        details = {
            "eval_mode": eval_mode,
            "target_solution": str(expected_solution) if expected_solution else "none",
        }

        if expected_solution is not None:
            correct_expr = parsed_options[question.correct_option]
            if not are_values_equivalent(correct_expr, expected_solution):
                errors.append(
                    f"Correct option '{question.correct_option}' ('{question.options[question.correct_option]}') "
                    f"does not equal computed truth '{expected_solution}'"
                )

            for distractor_key, distractor_expr in parsed_options.items():
                if (
                    distractor_key != question.correct_option
                    and distractor_expr is not None
                    and are_values_equivalent(distractor_expr, expected_solution)
                ):
                    errors.append(
                        f"Distractor '{distractor_key}' ('{question.options[distractor_key]}') "
                        f"equals the correct solution '{expected_solution}'"
                    )

        return MathValidationResult(
            is_valid=len(errors) == 0, errors=errors, details=details
        )
