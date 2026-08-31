from quiz.contracts.models import DistractorDetail, QuizQuestion

PRE_ALGEBRA_TWO_STEP_A_QUESTIONS: list[QuizQuestion] = [
    QuizQuestion(
        id="seed_prealg_two_01",
        topic="pre_algebra",
        subconcept="two_step_equations",
        question_text="¿Cuál es el valor de x en: 2*x + 4 = 12?",
        options={"A": "4", "B": "8", "C": "2", "D": "6"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="forgot_division",
                explanation="Restaste 4 (12 - 4 = 8) pero olvidaste dividir entre 2.",
            ),
            "C": DistractorDetail(
                misconception="divided_before_subtracting",
                explanation="Dividiste 12 / 2 = 6 y restaste 4 sin dividir el 4 entre 2.",
            ),
            "D": DistractorDetail(
                misconception="subtracted_instead_of_divided",
                explanation="Restaste 2 en lugar de dividir 8 entre 2.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_prealg_two_02",
        topic="pre_algebra",
        subconcept="two_step_equations",
        question_text="¿Cuál es el valor de x en: 3*x + 6 = 21?",
        options={"A": "15", "B": "5", "C": "1", "D": "12"},
        correct_option="B",
        distractors={
            "A": DistractorDetail(
                misconception="forgot_division",
                explanation="Restaste 6 (21 - 6 = 15) pero no dividiste entre 3.",
            ),
            "C": DistractorDetail(
                misconception="divided_before_subtracting",
                explanation="Dividiste 21 / 3 = 7 y restaste 6 sin dividir el 6 entre 3.",
            ),
            "D": DistractorDetail(
                misconception="subtracted_instead_of_divided",
                explanation="Restaste 3 en vez de dividir 15 / 3.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_prealg_two_03",
        topic="pre_algebra",
        subconcept="two_step_equations",
        question_text="¿Cuál es el valor de x en: 4*x - 8 = 16?",
        options={"A": "24", "B": "2", "C": "6", "D": "4"},
        correct_option="C",
        distractors={
            "A": DistractorDetail(
                misconception="forgot_division",
                explanation="Sumaste 8 (16 + 8 = 24) pero olvidaste dividir entre 4.",
            ),
            "B": DistractorDetail(
                misconception="sign_inversion_error",
                explanation="Restaste 8 en vez de sumar 8 para cancelar el -8.",
            ),
            "D": DistractorDetail(
                misconception="divided_before_subtracting",
                explanation="Dividiste 16 / 4 = 4 ignorando el término -8.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_prealg_two_04",
        topic="pre_algebra",
        subconcept="two_step_equations",
        question_text="¿Cuál es el valor de x en: 5*x + 10 = 35?",
        options={"A": "25", "B": "-3", "C": "20", "D": "5"},
        correct_option="D",
        distractors={
            "A": DistractorDetail(
                misconception="forgot_division",
                explanation="Restaste 10 (35 - 10 = 25) pero no dividiste entre 5.",
            ),
            "B": DistractorDetail(
                misconception="divided_before_subtracting",
                explanation="Dividiste 35 / 5 = 7 y luego restaste 10 sin dividirlo entre 5.",
            ),
            "C": DistractorDetail(
                misconception="subtracted_instead_of_divided",
                explanation="Restaste 5 en vez de dividir 25 / 5.",
            ),
        },
    ),
]
