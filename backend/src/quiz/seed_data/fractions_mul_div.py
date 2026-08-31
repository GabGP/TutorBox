from quiz.contracts.models import DistractorDetail, QuizQuestion

FRACTIONS_MUL_DIV_QUESTIONS: list[QuizQuestion] = [
    QuizQuestion(
        id="seed_frac_mul_01",
        topic="fractions",
        subconcept="multiplication_division",
        question_text="¿Cuánto es 2/3 * 3/4?",
        options={"A": "1/2", "B": "8/9", "C": "3/2", "D": "1/4"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="cross_multiplied_for_product",
                explanation="Multiplicaste cruzado en vez de multiplicar en línea recta.",
            ),
            "C": DistractorDetail(
                misconception="multiplied_only_numerators",
                explanation="Multiplicaste solo numeradores sin multiplicar denominadores.",
            ),
            "D": DistractorDetail(
                misconception="forgot_to_invert_divisor",
                explanation="Dividiste en lugar de multiplicar directamente.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_frac_mul_02",
        topic="fractions",
        subconcept="multiplication_division",
        question_text="¿Cuánto es 1/2 * 2/5?",
        options={"A": "5/4", "B": "1/5", "C": "1", "D": "1/10"},
        correct_option="B",
        distractors={
            "A": DistractorDetail(
                misconception="cross_multiplied_for_product",
                explanation="Multiplicaste en cruz 1*5 / 2*2.",
            ),
            "C": DistractorDetail(
                misconception="multiplied_only_numerators",
                explanation="Multiplicaste solo numeradores.",
            ),
            "D": DistractorDetail(
                misconception="forgot_to_invert_divisor",
                explanation="Cometiste un error al simplificar el producto.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_frac_div_01",
        topic="fractions",
        subconcept="multiplication_division",
        question_text="¿Cuánto es (3/4) / (1/2)?",
        options={"A": "3/8", "B": "1/2", "C": "3/2", "D": "3/4"},
        correct_option="C",
        distractors={
            "A": DistractorDetail(
                misconception="forgot_to_invert_divisor",
                explanation="Multiplicaste en línea recta sin invertir el divisor.",
            ),
            "B": DistractorDetail(
                misconception="cross_multiplied_for_product",
                explanation="Calculaste mal la inversión del divisor.",
            ),
            "D": DistractorDetail(
                misconception="multiplied_only_numerators",
                explanation="Dividiste solo numeradores manteniendo el denominador.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_frac_div_02",
        topic="fractions",
        subconcept="multiplication_division",
        question_text="¿Cuánto es (2/5) / (2/3)?",
        options={"A": "4/15", "B": "2/15", "C": "1", "D": "3/5"},
        correct_option="D",
        distractors={
            "A": DistractorDetail(
                misconception="forgot_to_invert_divisor",
                explanation="Multiplicaste 2*2 y 5*3 en vez de invertir 2/3.",
            ),
            "B": DistractorDetail(
                misconception="cross_multiplied_for_product",
                explanation="Multiplicaste de forma incorrecta los factores cruzados.",
            ),
            "C": DistractorDetail(
                misconception="multiplied_only_numerators",
                explanation="Dividiste solo los numeradores iguales dando 1.",
            ),
        },
    ),
]
