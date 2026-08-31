from quiz.contracts.models import DistractorDetail, QuizQuestion

PRE_ALGEBRA_LINEAR_MUL_QUESTIONS: list[QuizQuestion] = [
    QuizQuestion(
        id="seed_prealg_one_05",
        topic="pre_algebra",
        subconcept="one_step_equations",
        question_text="¿Cuál es el valor de x en: 3*x = 15?",
        options={"A": "45", "B": "12", "C": "5", "D": "15"},
        correct_option="C",
        distractors={
            "A": DistractorDetail(
                misconception="wrong_inverse_operation",
                explanation="Multiplicaste 15 * 3 en vez de dividir entre 3.",
            ),
            "B": DistractorDetail(
                misconception="sign_flip_error",
                explanation="Restaste 15 - 3 en lugar de dividir.",
            ),
            "D": DistractorDetail(
                misconception="applied_op_to_one_side_only",
                explanation="Ignoraste la operación inversa para despejar x.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_prealg_one_06",
        topic="pre_algebra",
        subconcept="one_step_equations",
        question_text="¿Cuál es el valor de x en: x / 2 = 6?",
        options={"A": "3", "B": "8", "C": "6", "D": "12"},
        correct_option="D",
        distractors={
            "A": DistractorDetail(
                misconception="wrong_inverse_operation",
                explanation="Dividiste 6 / 2 en vez de multiplicar por 2.",
            ),
            "B": DistractorDetail(
                misconception="sign_flip_error",
                explanation="Sumaste 6 + 2 en lugar de multiplicar por 2.",
            ),
            "C": DistractorDetail(
                misconception="applied_op_to_one_side_only",
                explanation="No aplicaste la multiplicación en el lado derecho.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_prealg_one_07",
        topic="pre_algebra",
        subconcept="one_step_equations",
        question_text="¿Cuál es el valor de x en: 4*x = 24?",
        options={"A": "96", "B": "20", "C": "6", "D": "24"},
        correct_option="C",
        distractors={
            "A": DistractorDetail(
                misconception="wrong_inverse_operation",
                explanation="Multiplicaste 24 * 4 en vez de dividir 24 / 4.",
            ),
            "B": DistractorDetail(
                misconception="sign_flip_error",
                explanation="Restaste 24 - 4 en vez de dividir entre 4.",
            ),
            "D": DistractorDetail(
                misconception="applied_op_to_one_side_only",
                explanation="Ignoraste el coeficiente 4 al despejar x.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_prealg_one_08",
        topic="pre_algebra",
        subconcept="one_step_equations",
        question_text="¿Cuál es el valor de x en: x / 3 = 5?",
        options={"A": "2", "B": "8", "C": "5", "D": "15"},
        correct_option="D",
        distractors={
            "A": DistractorDetail(
                misconception="wrong_inverse_operation",
                explanation="Restaste 5 - 3 en vez de multiplicar 5 * 3.",
            ),
            "B": DistractorDetail(
                misconception="sign_flip_error",
                explanation="Sumaste 5 + 3 en lugar de multiplicar por 3.",
            ),
            "C": DistractorDetail(
                misconception="applied_op_to_one_side_only",
                explanation="Olvidaste multiplicar el miembro derecho por 3.",
            ),
        },
    ),
]
