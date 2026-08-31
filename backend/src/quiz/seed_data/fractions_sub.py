from quiz.contracts.models import DistractorDetail, QuizQuestion

FRACTIONS_SUB_QUESTIONS: list[QuizQuestion] = [
    QuizQuestion(
        id="seed_frac_sub_01",
        topic="fractions",
        subconcept="addition_subtraction",
        question_text="¿Cuánto es 3/5 - 1/5?",
        options={"A": "2/10", "B": "2/5", "C": "4/5", "D": "3/25"},
        correct_option="B",
        distractors={
            "A": DistractorDetail(
                misconception="added_denominators",
                explanation="Sumaste los denominadores 5 + 5 = 10 al restar fracciones.",
            ),
            "C": DistractorDetail(
                misconception="ignored_common_denominator",
                explanation="Sumaste los numeradores 3 + 1 = 4 en lugar de restarlos.",
            ),
            "D": DistractorDetail(
                misconception="subtracted_denominators",
                explanation="Multiplicaste numeradores y denominadores 3*1 / 5*5 = 3/25 en vez de restar.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_frac_sub_02",
        topic="fractions",
        subconcept="addition_subtraction",
        question_text="¿Cuánto es 5/8 - 2/8?",
        options={"A": "3/16", "B": "7/8", "C": "5/32", "D": "3/8"},
        correct_option="D",
        distractors={
            "A": DistractorDetail(
                misconception="added_denominators",
                explanation="Sumaste los denominadores 8 + 8 = 16 al restar.",
            ),
            "B": DistractorDetail(
                misconception="ignored_common_denominator",
                explanation="Sumaste 5 + 2 = 7 en lugar de restar.",
            ),
            "C": DistractorDetail(
                misconception="subtracted_denominators",
                explanation="Multiplicaste numeradores y denominadores 5*2 / 8*8 = 10/64 = 5/32 en vez de restar.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_frac_sub_03",
        topic="fractions",
        subconcept="addition_subtraction",
        question_text="¿Cuánto es 4/9 - 1/9?",
        options={"A": "1/6", "B": "1/3", "C": "5/9", "D": "2/9"},
        correct_option="B",
        distractors={
            "A": DistractorDetail(
                misconception="added_denominators",
                explanation="Sumaste los denominadores resultando en 3/18 = 1/6.",
            ),
            "C": DistractorDetail(
                misconception="ignored_common_denominator",
                explanation="Sumaste 4 + 1 = 5 en vez de restar 4 - 1 = 3.",
            ),
            "D": DistractorDetail(
                misconception="subtracted_denominators",
                explanation="Restaste erróneamente en el numerador.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_frac_sub_04",
        topic="fractions",
        subconcept="addition_subtraction",
        question_text="¿Cuánto es 7/12 - 2/12?",
        options={"A": "5/24", "B": "3/4", "C": "7/72", "D": "5/12"},
        correct_option="D",
        distractors={
            "A": DistractorDetail(
                misconception="added_denominators",
                explanation="Sumaste los denominadores 12 + 12 = 24.",
            ),
            "B": DistractorDetail(
                misconception="ignored_common_denominator",
                explanation="Sumaste 7 + 2 = 9 (9/12 = 3/4) en vez de restar.",
            ),
            "C": DistractorDetail(
                misconception="subtracted_denominators",
                explanation="Multiplicaste numeradores y denominadores 7*2 / 12*12 = 14/144 = 7/72 en lugar de restar.",
            ),
        },
    ),
]
