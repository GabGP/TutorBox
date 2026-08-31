from quiz.contracts.models import DistractorDetail, QuizQuestion

ARITHMETIC_ADD_QUESTIONS: list[QuizQuestion] = [
    QuizQuestion(
        id="seed_arith_add_01",
        topic="arithmetic",
        subconcept="addition_subtraction",
        question_text="¿Cuánto es 54 + 38?",
        options={"A": "82", "B": "16", "C": "92", "D": "812"},
        correct_option="C",
        distractors={
            "A": DistractorDetail(
                misconception="alignment_error",
                explanation="Olvidaste sumar la decena que llevabas.",
            ),
            "B": DistractorDetail(
                misconception="added_instead_of_subtracted",
                explanation="Restaste 54 - 38 en vez de sumarlos.",
            ),
            "D": DistractorDetail(
                misconception="borrowing_error",
                explanation="Escribiste el 12 completo al lado de la suma de decenas.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_arith_add_02",
        topic="arithmetic",
        subconcept="addition_subtraction",
        question_text="¿Cuánto es 67 + 29?",
        options={"A": "96", "B": "86", "C": "38", "D": "95"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="alignment_error",
                explanation="No sumaste la decena que llevabas de 7 + 9.",
            ),
            "C": DistractorDetail(
                misconception="added_instead_of_subtracted",
                explanation="Restaste los valores en vez de realizar la suma.",
            ),
            "D": DistractorDetail(
                misconception="sign_error",
                explanation="Calculaste mal la suma de las unidades 7 + 9.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_arith_add_03",
        topic="arithmetic",
        subconcept="addition_subtraction",
        question_text="¿Cuánto es 36 + 48?",
        options={"A": "74", "B": "12", "C": "84", "D": "714"},
        correct_option="C",
        distractors={
            "A": DistractorDetail(
                misconception="alignment_error",
                explanation="Olvidaste sumar la decena llevada.",
            ),
            "B": DistractorDetail(
                misconception="added_instead_of_subtracted",
                explanation="Restaste en lugar de sumar los números.",
            ),
            "D": DistractorDetail(
                misconception="borrowing_error",
                explanation="Escribiste 14 completo en las unidades sin reagrupar.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_arith_add_04",
        topic="arithmetic",
        subconcept="addition_subtraction",
        question_text="¿Cuánto es 49 + 25?",
        options={"A": "74", "B": "64", "C": "24", "D": "614"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="alignment_error",
                explanation="No sumaste la decena que llevas de 9 + 5.",
            ),
            "C": DistractorDetail(
                misconception="added_instead_of_subtracted",
                explanation="Restaste los números en lugar de sumarlos.",
            ),
            "D": DistractorDetail(
                misconception="borrowing_error",
                explanation="Escribiste 14 sin reagrupar decenas.",
            ),
        },
    ),
]
