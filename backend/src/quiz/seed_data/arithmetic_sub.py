from quiz.contracts.models import DistractorDetail, QuizQuestion

ARITHMETIC_SUB_QUESTIONS: list[QuizQuestion] = [
    QuizQuestion(
        id="seed_arith_sub_01",
        topic="arithmetic",
        subconcept="addition_subtraction",
        question_text="¿Cuánto es 45 - 28?",
        options={"A": "17", "B": "27", "C": "73", "D": "23"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="borrowing_error",
                explanation="Al restar no desagrupaste las decenas correctamente.",
            ),
            "C": DistractorDetail(
                misconception="added_instead_of_subtracted",
                explanation="Sumaste los números en lugar de restarlos.",
            ),
            "D": DistractorDetail(
                misconception="sign_error",
                explanation="Restaste el menor del mayor en cada columna sin desagrupar.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_arith_sub_02",
        topic="arithmetic",
        subconcept="addition_subtraction",
        question_text="¿Cuánto es 72 - 39?",
        options={"A": "43", "B": "33", "C": "111", "D": "47"},
        correct_option="B",
        distractors={
            "A": DistractorDetail(
                misconception="borrowing_error",
                explanation="Olvidaste restar 1 a las decenas después de desagrupar.",
            ),
            "C": DistractorDetail(
                misconception="added_instead_of_subtracted",
                explanation="Sumaste 72 + 39 en lugar de restar.",
            ),
            "D": DistractorDetail(
                misconception="sign_error",
                explanation="Restaste 9 - 2 = 7 en unidades y 7 - 3 = 4 en decenas sin desagrupar.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_arith_sub_03",
        topic="arithmetic",
        subconcept="addition_subtraction",
        question_text="¿Cuánto es 83 - 47?",
        options={"A": "44", "B": "46", "C": "130", "D": "36"},
        correct_option="D",
        distractors={
            "A": DistractorDetail(
                misconception="sign_error",
                explanation="Restaste 7 - 3 en las unidades sin reagrupar decenas.",
            ),
            "B": DistractorDetail(
                misconception="borrowing_error",
                explanation="Desagrupaste las unidades pero no redujiste las decenas.",
            ),
            "C": DistractorDetail(
                misconception="added_instead_of_subtracted",
                explanation="Efectuaste una suma en vez de una resta.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_arith_sub_04",
        topic="arithmetic",
        subconcept="addition_subtraction",
        question_text="¿Cuánto es 60 - 27?",
        options={"A": "43", "B": "47", "C": "87", "D": "33"},
        correct_option="D",
        distractors={
            "A": DistractorDetail(
                misconception="borrowing_error",
                explanation="No restaste la decena que prestaste al cero.",
            ),
            "B": DistractorDetail(
                misconception="sign_error",
                explanation="Restaste 7 - 0 = 7 en unidades y 6 - 2 = 4 en decenas sin desagrupar.",
            ),
            "C": DistractorDetail(
                misconception="added_instead_of_subtracted",
                explanation="Sumaste 60 + 27 en vez de restar.",
            ),
        },
    ),
]
