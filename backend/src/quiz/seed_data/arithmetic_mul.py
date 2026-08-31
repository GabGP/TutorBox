from quiz.contracts.models import DistractorDetail, QuizQuestion

ARITHMETIC_MUL_QUESTIONS: list[QuizQuestion] = [
    QuizQuestion(
        id="seed_arith_mul_01",
        topic="arithmetic",
        subconcept="multiplication_division",
        question_text="¿Cuánto es 23 * 4?",
        options={"A": "82", "B": "27", "C": "92", "D": "812"},
        correct_option="C",
        distractors={
            "A": DistractorDetail(
                misconception="forgot_carry",
                explanation="Multiplicaste 3 * 4 = 12 pero no sumaste el 1 que llevabas a las decenas.",
            ),
            "B": DistractorDetail(
                misconception="remainder_ignored",
                explanation="Sumaste 23 + 4 en lugar de multiplicar.",
            ),
            "D": DistractorDetail(
                misconception="table_lookup_error",
                explanation="Escribiste el 12 completo al lado del 8 sin reagrupar decenas.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_arith_mul_02",
        topic="arithmetic",
        subconcept="multiplication_division",
        question_text="¿Cuánto es 24 * 3?",
        options={"A": "62", "B": "72", "C": "27", "D": "612"},
        correct_option="B",
        distractors={
            "A": DistractorDetail(
                misconception="forgot_carry",
                explanation="Multiplicaste 4 * 3 = 12 pero olvidaste sumar el 1 a las decenas.",
            ),
            "C": DistractorDetail(
                misconception="remainder_ignored",
                explanation="Sumaste 24 + 3 en vez de multiplicar.",
            ),
            "D": DistractorDetail(
                misconception="table_lookup_error",
                explanation="Escribiste el 12 de unidades sin reagrupar a las decenas.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_arith_mul_03",
        topic="arithmetic",
        subconcept="multiplication_division",
        question_text="¿Cuánto es 14 * 3?",
        options={"A": "42", "B": "32", "C": "17", "D": "45"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="forgot_carry",
                explanation="Olvidaste sumar el 1 que llevabas al multiplicar decenas.",
            ),
            "C": DistractorDetail(
                misconception="table_lookup_error",
                explanation="Sumaste 14 + 3 en lugar de multiplicar.",
            ),
            "D": DistractorDetail(
                misconception="table_lookup_error",
                explanation="Calculaste mal 4 * 3.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_arith_mul_04",
        topic="arithmetic",
        subconcept="multiplication_division",
        question_text="¿Cuánto es 16 * 4?",
        options={"A": "44", "B": "20", "C": "64", "D": "68"},
        correct_option="C",
        distractors={
            "A": DistractorDetail(
                misconception="forgot_carry",
                explanation="Olvidaste sumar el 2 que llevabas de 6 * 4.",
            ),
            "B": DistractorDetail(
                misconception="table_lookup_error",
                explanation="Sumaste 16 + 4 en lugar de multiplicar.",
            ),
            "D": DistractorDetail(
                misconception="table_lookup_error",
                explanation="Multiplicaste con un error en las unidades.",
            ),
        },
    ),
]
