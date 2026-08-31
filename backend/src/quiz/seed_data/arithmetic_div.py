from quiz.contracts.models import DistractorDetail, QuizQuestion

ARITHMETIC_DIV_QUESTIONS: list[QuizQuestion] = [
    QuizQuestion(
        id="seed_arith_div_01",
        topic="arithmetic",
        subconcept="multiplication_division",
        question_text="¿Cuánto es 24 / 6?",
        options={"A": "18", "B": "144", "C": "4", "D": "3"},
        correct_option="C",
        distractors={
            "A": DistractorDetail(
                misconception="remainder_ignored",
                explanation="Restaste 24 - 6 = 18 una sola vez en vez de completar la división.",
            ),
            "B": DistractorDetail(
                misconception="inverted_division",
                explanation="Multiplicaste 24 * 6 en vez de dividir.",
            ),
            "D": DistractorDetail(
                misconception="table_lookup_error",
                explanation="Calculaste 18 / 6 en lugar de 24 / 6.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_arith_div_02",
        topic="arithmetic",
        subconcept="multiplication_division",
        question_text="¿Cuánto es 56 / 8?",
        options={"A": "6", "B": "48", "C": "448", "D": "7"},
        correct_option="D",
        distractors={
            "A": DistractorDetail(
                misconception="table_lookup_error",
                explanation="Confundiste 56 / 8 con 48 / 8.",
            ),
            "B": DistractorDetail(
                misconception="remainder_ignored",
                explanation="Restaste 56 - 8 = 48 una sola vez en lugar de dividir.",
            ),
            "C": DistractorDetail(
                misconception="inverted_division",
                explanation="Multiplicaste en vez de dividir.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_arith_div_03",
        topic="arithmetic",
        subconcept="multiplication_division",
        question_text="¿Cuánto es 72 / 9?",
        options={"A": "7", "B": "8", "C": "63", "D": "648"},
        correct_option="B",
        distractors={
            "A": DistractorDetail(
                misconception="table_lookup_error",
                explanation="Confundiste 72 / 9 con 63 / 9.",
            ),
            "C": DistractorDetail(
                misconception="remainder_ignored",
                explanation="Restaste 72 - 9 = 63 una sola vez en lugar de dividir.",
            ),
            "D": DistractorDetail(
                misconception="inverted_division",
                explanation="Multiplicaste 72 * 9 en lugar de dividir.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_arith_div_04",
        topic="arithmetic",
        subconcept="multiplication_division",
        question_text="¿Cuánto es 45 / 5?",
        options={"A": "8", "B": "40", "C": "225", "D": "9"},
        correct_option="D",
        distractors={
            "A": DistractorDetail(
                misconception="table_lookup_error",
                explanation="Confundiste 45 / 5 con 40 / 5.",
            ),
            "B": DistractorDetail(
                misconception="remainder_ignored",
                explanation="Restaste 45 - 5 = 40 una sola vez en vez de dividir.",
            ),
            "C": DistractorDetail(
                misconception="inverted_division",
                explanation="Multiplicaste 45 * 5 en vez de dividir.",
            ),
        },
    ),
]
