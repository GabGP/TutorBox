from quiz.contracts.models import DistractorDetail, QuizQuestion

FRACTIONS_ADD_QUESTIONS: list[QuizQuestion] = [
    QuizQuestion(
        id="seed_frac_add_01",
        topic="fractions",
        subconcept="addition_subtraction",
        question_text="¿Cuánto es 1/4 + 2/4?",
        options={"A": "3/4", "B": "3/8", "C": "1/2", "D": "1/4"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="added_denominators",
                explanation="Sumaste los denominadores (4 + 4 = 8) en vez de mantener el común.",
            ),
            "C": DistractorDetail(
                misconception="ignored_common_denominator",
                explanation="Multiplicaste o combinaste numeradores sin sumar correctamente.",
            ),
            "D": DistractorDetail(
                misconception="subtracted_denominators",
                explanation="Restaste numeradores en lugar de sumarlos.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_frac_add_02",
        topic="fractions",
        subconcept="addition_subtraction",
        question_text="¿Cuánto es 2/7 + 3/7?",
        options={"A": "5/14", "B": "1/7", "C": "5/7", "D": "6/7"},
        correct_option="C",
        distractors={
            "A": DistractorDetail(
                misconception="added_denominators",
                explanation="Sumaste los denominadores 7 + 7 = 14.",
            ),
            "B": DistractorDetail(
                misconception="ignored_common_denominator",
                explanation="Restaste los numeradores en vez de sumarlos.",
            ),
            "D": DistractorDetail(
                misconception="subtracted_denominators",
                explanation="Multiplicaste numeradores 2 * 3 = 6.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_frac_add_03",
        topic="fractions",
        subconcept="addition_subtraction",
        question_text="¿Cuánto es 1/5 + 2/5?",
        options={"A": "3/5", "B": "3/10", "C": "2/25", "D": "1/5"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="added_denominators",
                explanation="Sumaste 5 + 5 = 10 en el denominador en vez de mantener el común.",
            ),
            "C": DistractorDetail(
                misconception="ignored_common_denominator",
                explanation="Multiplicaste numeradores y denominadores 1*2 / 5*5 = 2/25 en vez de sumar.",
            ),
            "D": DistractorDetail(
                misconception="subtracted_denominators",
                explanation="Restaste numeradores 2 - 1 = 1/5 en lugar de sumarlos.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_frac_add_04",
        topic="fractions",
        subconcept="addition_subtraction",
        question_text="¿Cuánto es 3/10 + 4/10?",
        options={"A": "7/20", "B": "1/10", "C": "7/10", "D": "3/25"},
        correct_option="C",
        distractors={
            "A": DistractorDetail(
                misconception="added_denominators",
                explanation="Sumaste 10 + 10 = 20 en el denominador.",
            ),
            "B": DistractorDetail(
                misconception="ignored_common_denominator",
                explanation="Restaste 4 - 3 = 1/10 en vez de sumar 3 + 4.",
            ),
            "D": DistractorDetail(
                misconception="subtracted_denominators",
                explanation="Multiplicaste las fracciones 3*4 / 10*10 = 12/100 = 3/25 en lugar de sumarlas.",
            ),
        },
    ),
]
