"""Curated, mathematically verified seed questions for TutorBox."""

from quiz.contracts.models import QuizQuestion
from quiz.seed_data.arithmetic_add import ARITHMETIC_ADD_QUESTIONS
from quiz.seed_data.arithmetic_div import ARITHMETIC_DIV_QUESTIONS
from quiz.seed_data.arithmetic_mul import ARITHMETIC_MUL_QUESTIONS
from quiz.seed_data.arithmetic_sub import ARITHMETIC_SUB_QUESTIONS
from quiz.seed_data.decimals import DECIMALS_QUESTIONS
from quiz.seed_data.fractions_add import FRACTIONS_ADD_QUESTIONS
from quiz.seed_data.fractions_mul_div import FRACTIONS_MUL_DIV_QUESTIONS
from quiz.seed_data.fractions_simplification import (
    FRACTIONS_SIMPLIFICATION_QUESTIONS,
)
from quiz.seed_data.fractions_sub import FRACTIONS_SUB_QUESTIONS
from quiz.seed_data.order_of_ops_advanced import ORDER_OF_OPS_ADVANCED_QUESTIONS
from quiz.seed_data.order_of_ops_basic import ORDER_OF_OPS_BASIC_QUESTIONS
from quiz.seed_data.percentages import PERCENTAGES_QUESTIONS
from quiz.seed_data.pre_algebra_linear_add import (
    PRE_ALGEBRA_LINEAR_ADD_QUESTIONS,
)
from quiz.seed_data.pre_algebra_linear_mul import (
    PRE_ALGEBRA_LINEAR_MUL_QUESTIONS,
)
from quiz.seed_data.pre_algebra_two_step_a import (
    PRE_ALGEBRA_TWO_STEP_A_QUESTIONS,
)
from quiz.seed_data.pre_algebra_two_step_b import (
    PRE_ALGEBRA_TWO_STEP_B_QUESTIONS,
)
from quiz.seed_data.seeder import seed_question_bank

SEED_QUESTIONS: list[QuizQuestion] = [
    *ARITHMETIC_ADD_QUESTIONS,
    *ARITHMETIC_SUB_QUESTIONS,
    *ARITHMETIC_MUL_QUESTIONS,
    *ARITHMETIC_DIV_QUESTIONS,
    *ORDER_OF_OPS_BASIC_QUESTIONS,
    *ORDER_OF_OPS_ADVANCED_QUESTIONS,
    *FRACTIONS_ADD_QUESTIONS,
    *FRACTIONS_SUB_QUESTIONS,
    *FRACTIONS_MUL_DIV_QUESTIONS,
    *FRACTIONS_SIMPLIFICATION_QUESTIONS,
    *PRE_ALGEBRA_LINEAR_ADD_QUESTIONS,
    *PRE_ALGEBRA_LINEAR_MUL_QUESTIONS,
    *PRE_ALGEBRA_TWO_STEP_A_QUESTIONS,
    *PRE_ALGEBRA_TWO_STEP_B_QUESTIONS,
    *DECIMALS_QUESTIONS,
    *PERCENTAGES_QUESTIONS,
]

__all__ = [
    "ARITHMETIC_ADD_QUESTIONS",
    "ARITHMETIC_DIV_QUESTIONS",
    "ARITHMETIC_MUL_QUESTIONS",
    "ARITHMETIC_SUB_QUESTIONS",
    "DECIMALS_QUESTIONS",
    "FRACTIONS_ADD_QUESTIONS",
    "FRACTIONS_MUL_DIV_QUESTIONS",
    "FRACTIONS_SIMPLIFICATION_QUESTIONS",
    "FRACTIONS_SUB_QUESTIONS",
    "ORDER_OF_OPS_ADVANCED_QUESTIONS",
    "ORDER_OF_OPS_BASIC_QUESTIONS",
    "PERCENTAGES_QUESTIONS",
    "PRE_ALGEBRA_LINEAR_ADD_QUESTIONS",
    "PRE_ALGEBRA_LINEAR_MUL_QUESTIONS",
    "PRE_ALGEBRA_TWO_STEP_A_QUESTIONS",
    "PRE_ALGEBRA_TWO_STEP_B_QUESTIONS",
    "SEED_QUESTIONS",
    "seed_question_bank",
]
