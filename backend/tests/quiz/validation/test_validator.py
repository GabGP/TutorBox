from src.quiz.contracts.models import QuizQuestion
from src.quiz.validation.validator import MathValidatorInterface, SymPyMathValidator


def create_question(
    text: str,
    options: dict[str, str],
    correct: str,
    topic: str = "arithmetic",
    subconcept: str = "order_of_operations",
) -> QuizQuestion:
    distractors = {}
    for key in ["A", "B", "C", "D"]:
        if key != correct:
            distractors[key] = {
                "misconception": f"error_{key}",
                "explanation": f"Explicacion para {key}",
            }
    return QuizQuestion.model_validate(
        {
            "id": "q_test_01",
            "topic": topic,
            "subconcept": subconcept,
            "question_text": text,
            "options": options,
            "correct_option": correct,
            "distractors": distractors,
        }
    )


def test_validator_arithmetic_valid():
    validator = SymPyMathValidator()
    q = create_question(
        text="¿Cuál es el resultado de 3 + 4 * 2?",
        options={"A": "11", "B": "14", "C": "10", "D": "24"},
        correct="A",
    )
    result = validator.validate_question_math(q)
    assert result.is_valid is True
    assert result.details["eval_mode"] == "arithmetic"
    assert result.details["target_solution"] == "11"
    assert len(result.errors) == 0


def test_validator_linear_equation_valid():
    validator = SymPyMathValidator()
    q = create_question(
        text="¿Cuál es el valor de x en la ecuación 2x + 4 = 12?",
        options={"A": "4", "B": "8", "C": "3", "D": "6"},
        correct="A",
        topic="pre_algebra",
        subconcept="two_step_equations",
    )
    result = validator.validate_question_math(q)
    assert result.is_valid is True
    assert result.details["eval_mode"] == "equation"
    assert result.details["target_solution"] == "4"


def test_validator_fractions_and_spanish_symbols():
    validator = SymPyMathValidator()
    q = create_question(
        text="Calcula 12 ÷ 3 + 4 × 2.",
        options={"A": "12", "B": "8", "C": "14", "D": "20"},
        correct="A",
    )
    result = validator.validate_question_math(q)
    assert result.is_valid is True
    assert result.details["target_solution"] == "12"


def test_validator_fraction_simplification():
    validator = SymPyMathValidator()
    q = create_question(
        text="Calcula 1/2 + 1/4.",
        options={"A": "3/4", "B": "2/6", "C": "1/4", "D": "1"},
        correct="A",
        topic="fractions",
    )
    result = validator.validate_question_math(q)
    assert result.is_valid is True


def test_validator_correct_option_mismatch():
    validator = SymPyMathValidator()
    q = create_question(
        text="¿Cuánto es 3 + 4 * 2?",
        options={"A": "11", "B": "14", "C": "10", "D": "24"},
        correct="B",
    )
    result = validator.validate_question_math(q)
    assert result.is_valid is False
    assert any("does not equal computed truth" in err for err in result.errors)


def test_validator_distractor_collides_with_solution():
    validator = SymPyMathValidator()
    q = create_question(
        text="¿Cuánto es 3 + 4 * 2?",
        options={"A": "11", "B": "14", "C": "11", "D": "24"},
        correct="A",
    )
    result = validator.validate_question_math(q)
    assert result.is_valid is False
    assert any("Duplicate option values" in err for err in result.errors)
    assert any("equals the correct solution" in err for err in result.errors)


def test_validator_equation_option_with_variable_prefix():
    validator = SymPyMathValidator()
    q = create_question(
        text="Resuelve x - 7 = 15",
        options={"A": "x = 22", "B": "x = 8", "C": "x = 10", "D": "x = -8"},
        correct="A",
        topic="pre_algebra",
        subconcept="one_step_equations",
    )
    result = validator.validate_question_math(q)
    assert result.is_valid is True


def test_validator_conceptual_question_without_formula():
    validator = SymPyMathValidator()
    q = create_question(
        text="¿Qué propiedad indica que el orden de los factores no altera el producto?",
        options={
            "A": "Propiedad Conmutativa",
            "B": "Propiedad Asociativa",
            "C": "Propiedad Distributiva",
            "D": "Elemento Neutro",
        },
        correct="A",
        topic="math_concepts",
        subconcept="properties",
    )
    result = validator.validate_question_math(q)
    assert result.is_valid is True
    assert result.details["eval_mode"] == "none"


def test_validator_conceptual_duplicate_options_detected():
    validator = SymPyMathValidator()
    q = create_question(
        text="¿Qué propiedad indica que el orden de los factores no altera el producto?",
        options={
            "A": "Propiedad Conmutativa",
            "B": "Propiedad Conmutativa",
            "C": "Propiedad Distributiva",
            "D": "Elemento Neutro",
        },
        correct="A",
        topic="math_concepts",
        subconcept="properties",
    )
    result = validator.validate_question_math(q)
    assert result.is_valid is False
    assert any("Duplicate option values" in err for err in result.errors)


def test_validator_rejects_arithmetic_drift_in_algebra_subconcept():
    validator = SymPyMathValidator()
    q = create_question(
        text="¿Cuál es el resultado de 3 + 4 * 2?",
        options={"A": "11", "B": "14", "C": "10", "D": "24"},
        correct="A",
        topic="pre_algebra",
        subconcept="two_step_equations",
    )
    result = validator.validate_question_math(q)
    assert result.is_valid is False
    assert any("Pedagogical mismatch" in err for err in result.errors)


def test_validator_interface_abstract():
    class DummyValidator(MathValidatorInterface):
        def validate_question_math(self, question: QuizQuestion):
            return super().validate_question_math(question)

    q = create_question(
        text="Sample",
        options={"A": "1", "B": "2", "C": "3", "D": "4"},
        correct="A",
    )
    dummy = DummyValidator()
    assert dummy.validate_question_math(q) is None
