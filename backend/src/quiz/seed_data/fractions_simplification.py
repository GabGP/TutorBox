from quiz.contracts.models import DistractorDetail, QuizQuestion

FRACTIONS_SIMPLIFICATION_QUESTIONS: list[QuizQuestion] = [
    QuizQuestion(
        id="seed_frac_smp_01",
        topic="fractions",
        subconcept="simplification",
        question_text="¿Cuánto es 4/8 simplificado?",
        options={"A": "1/2", "B": "1/8", "C": "1/3", "D": "1/4"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="divided_only_numerator",
                explanation="Dividiste el numerador entre 4 pero dejaste el denominador igual.",
            ),
            "C": DistractorDetail(
                misconception="subtracted_to_reduce",
                explanation="Restaste una cantidad al numerador y denominador en lugar de dividir.",
            ),
            "D": DistractorDetail(
                misconception="partial_factor_division",
                explanation="Dividiste solo entre 2 una vez o aplicaste factores dispares.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_frac_smp_02",
        topic="fractions",
        subconcept="simplification",
        question_text="¿Cuánto es 6/9 simplificado?",
        options={"A": "2/9", "B": "2/3", "C": "4/7", "D": "1/3"},
        correct_option="B",
        distractors={
            "A": DistractorDetail(
                misconception="divided_only_numerator",
                explanation="Dividiste 6 entre 3 pero no dividiste 9 entre 3.",
            ),
            "C": DistractorDetail(
                misconception="subtracted_to_reduce",
                explanation="Restaste 2 a ambos términos en lugar de dividir entre el MCD.",
            ),
            "D": DistractorDetail(
                misconception="partial_factor_division",
                explanation="Dividiste incorrectamente entre factores no compartidos.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_frac_smp_03",
        topic="fractions",
        subconcept="simplification",
        question_text="¿Cuánto es 5/10 simplificado?",
        options={"A": "1/10", "B": "3/8", "C": "1/2", "D": "2/5"},
        correct_option="C",
        distractors={
            "A": DistractorDetail(
                misconception="divided_only_numerator",
                explanation="Dividiste solo el numerador entre 5.",
            ),
            "B": DistractorDetail(
                misconception="subtracted_to_reduce",
                explanation="Restaste 2 arriba y abajo en vez de simplificar dividiendo.",
            ),
            "D": DistractorDetail(
                misconception="partial_factor_division",
                explanation="Dividiste el denominador entre 2 y el numerador no.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_frac_smp_04",
        topic="fractions",
        subconcept="simplification",
        question_text="¿Cuánto es 8/12 simplificado?",
        options={"A": "2/12", "B": "3/5", "C": "1/3", "D": "2/3"},
        correct_option="D",
        distractors={
            "A": DistractorDetail(
                misconception="divided_only_numerator",
                explanation="Dividiste solo el numerador 8 / 4 = 2.",
            ),
            "B": DistractorDetail(
                misconception="subtracted_to_reduce",
                explanation="Restaste cantidades arbitrarias para reducir la fracción.",
            ),
            "C": DistractorDetail(
                misconception="partial_factor_division",
                explanation="Dividiste de forma desigual numerador y denominador.",
            ),
        },
    ),
]
