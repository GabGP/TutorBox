from quiz.contracts.models import DistractorDetail, QuizQuestion

PRE_ALGEBRA_TWO_STEP_B_QUESTIONS: list[QuizQuestion] = [
    QuizQuestion(
        id="seed_prealg_two_05",
        topic="pre_algebra",
        subconcept="two_step_equations",
        question_text="¿Cuál es el valor de x en: 2*x + 10 = 24?",
        options={"A": "7", "B": "14", "C": "2", "D": "12"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="forgot_division",
                explanation="Restaste 10 de 24 pero olvidaste dividir entre 2.",
            ),
            "C": DistractorDetail(
                misconception="divided_before_subtracting",
                explanation="Dividiste 24 / 2 = 12 y restaste 10 sin dividir el 10 entre 2.",
            ),
            "D": DistractorDetail(
                misconception="subtracted_instead_of_divided",
                explanation="Restaste 2 en lugar de dividir entre 2.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_prealg_two_06",
        topic="pre_algebra",
        subconcept="two_step_equations",
        question_text="¿Cuál es el valor de x en: 3*x - 3 = 15?",
        options={"A": "18", "B": "6", "C": "4", "D": "5"},
        correct_option="B",
        distractors={
            "A": DistractorDetail(
                misconception="forgot_division",
                explanation="Sumaste 15 + 3 = 18 pero no dividiste entre 3.",
            ),
            "C": DistractorDetail(
                misconception="sign_inversion_error",
                explanation="Restaste 3 (15 - 3 = 12) y dividiste entre 3 = 4.",
            ),
            "D": DistractorDetail(
                misconception="divided_before_subtracting",
                explanation="Dividiste 15 / 3 = 5 ignorando la resta de 3.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_prealg_two_07",
        topic="pre_algebra",
        subconcept="two_step_equations",
        question_text="¿Cuál es el valor de x en: 4*x + 4 = 28?",
        options={"A": "24", "B": "3", "C": "6", "D": "20"},
        correct_option="C",
        distractors={
            "A": DistractorDetail(
                misconception="forgot_division",
                explanation="Restaste 28 - 4 = 24 pero no dividiste entre 4.",
            ),
            "B": DistractorDetail(
                misconception="divided_before_subtracting",
                explanation="Dividiste 28 / 4 = 7 y restaste 4 sin dividir el 4 entre 4.",
            ),
            "D": DistractorDetail(
                misconception="subtracted_instead_of_divided",
                explanation="Restaste 4 de 24 en lugar de dividir entre 4.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_prealg_two_08",
        topic="pre_algebra",
        subconcept="two_step_equations",
        question_text="¿Cuál es el valor de x en: 2*x - 6 = 14?",
        options={"A": "20", "B": "4", "C": "13", "D": "10"},
        correct_option="D",
        distractors={
            "A": DistractorDetail(
                misconception="forgot_division",
                explanation="Sumaste 14 + 6 = 20 pero olvidaste dividir entre 2.",
            ),
            "B": DistractorDetail(
                misconception="sign_inversion_error",
                explanation="Restaste 14 - 6 = 8 y dividiste entre 2 = 4.",
            ),
            "C": DistractorDetail(
                misconception="divided_before_subtracting",
                explanation="Dividiste 14 / 2 = 7 y sumaste 6 sin dividir el 6 entre 2.",
            ),
        },
    ),
]
