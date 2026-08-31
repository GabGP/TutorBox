from quiz.contracts.models import DistractorDetail, QuizQuestion

PRE_ALGEBRA_LINEAR_ADD_QUESTIONS: list[QuizQuestion] = [
    QuizQuestion(
        id="seed_prealg_one_01",
        topic="pre_algebra",
        subconcept="one_step_equations",
        question_text="¿Cuál es el valor de x en: x + 5 = 12?",
        options={"A": "7", "B": "17", "C": "60", "D": "12"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="sign_flip_error",
                explanation="Sumaste 5 en lugar de restar 5 al despejar x.",
            ),
            "C": DistractorDetail(
                misconception="wrong_inverse_operation",
                explanation="Multiplicaste por 5 en vez de restar 5.",
            ),
            "D": DistractorDetail(
                misconception="applied_op_to_one_side_only",
                explanation="Eliminaste el 5 de la izquierda sin restarlo de la derecha.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_prealg_one_02",
        topic="pre_algebra",
        subconcept="one_step_equations",
        question_text="¿Cuál es el valor de x en: x - 4 = 10?",
        options={"A": "6", "B": "14", "C": "40", "D": "10"},
        correct_option="B",
        distractors={
            "A": DistractorDetail(
                misconception="sign_flip_error",
                explanation="Restaste 4 en lugar de sumar 4 para cancelar la resta.",
            ),
            "C": DistractorDetail(
                misconception="wrong_inverse_operation",
                explanation="Multiplicaste 10 * 4 en vez de sumar 10 + 4.",
            ),
            "D": DistractorDetail(
                misconception="applied_op_to_one_side_only",
                explanation="Olvidaste sumar 4 al miembro derecho de la ecuación.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_prealg_one_03",
        topic="pre_algebra",
        subconcept="one_step_equations",
        question_text="¿Cuál es el valor de x en: x + 8 = 20?",
        options={"A": "12", "B": "28", "C": "160", "D": "20"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="sign_flip_error",
                explanation="Sumaste 20 + 8 en vez de restar 8.",
            ),
            "C": DistractorDetail(
                misconception="wrong_inverse_operation",
                explanation="Multiplicaste 20 * 8 en lugar de restar.",
            ),
            "D": DistractorDetail(
                misconception="applied_op_to_one_side_only",
                explanation="No restaste 8 al lado derecho de la ecuación.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_prealg_one_04",
        topic="pre_algebra",
        subconcept="one_step_equations",
        question_text="¿Cuál es el valor de x en: x - 7 = 9?",
        options={"A": "2", "B": "16", "C": "63", "D": "9"},
        correct_option="B",
        distractors={
            "A": DistractorDetail(
                misconception="sign_flip_error",
                explanation="Restaste 9 - 7 en lugar de sumar 9 + 7.",
            ),
            "C": DistractorDetail(
                misconception="wrong_inverse_operation",
                explanation="Multiplicaste en vez de aplicar la suma inversa.",
            ),
            "D": DistractorDetail(
                misconception="applied_op_to_one_side_only",
                explanation="Dejaste el valor de la derecha sin modificar.",
            ),
        },
    ),
]
