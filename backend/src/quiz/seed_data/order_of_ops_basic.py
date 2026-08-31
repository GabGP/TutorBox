from quiz.contracts.models import DistractorDetail, QuizQuestion

ORDER_OF_OPS_BASIC_QUESTIONS: list[QuizQuestion] = [
    QuizQuestion(
        id="seed_arith_ord_01",
        topic="arithmetic",
        subconcept="order_of_operations",
        question_text="¿Cuánto es 3 + 4 * 2?",
        options={"A": "11", "B": "14", "C": "18", "D": "24"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="left_to_right_precedence",
                explanation="Sumaste de izquierda a derecha (3 + 4 = 7) antes de multiplicar.",
            ),
            "C": DistractorDetail(
                misconception="addition_before_multiplication",
                explanation="Alteraste la precedencia sumando factores primero.",
            ),
            "D": DistractorDetail(
                misconception="ignored_parentheses",
                explanation="Multiplicaste todos los factores sin respetar la suma.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_arith_ord_02",
        topic="arithmetic",
        subconcept="order_of_operations",
        question_text="¿Cuánto es 10 - 2 * 3?",
        options={"A": "24", "B": "4", "C": "16", "D": "8"},
        correct_option="B",
        distractors={
            "A": DistractorDetail(
                misconception="left_to_right_precedence",
                explanation="Restaste primero 10 - 2 = 8 y luego multiplicaste por 3.",
            ),
            "C": DistractorDetail(
                misconception="addition_before_multiplication",
                explanation="Sumaste en vez de restar el producto.",
            ),
            "D": DistractorDetail(
                misconception="ignored_parentheses",
                explanation="No calculaste el producto 2 * 3 antes de la resta.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_arith_ord_03",
        topic="arithmetic",
        subconcept="order_of_operations",
        question_text="¿Cuánto es 6 + 8 / 2?",
        options={"A": "7", "B": "4", "C": "10", "D": "14"},
        correct_option="C",
        distractors={
            "A": DistractorDetail(
                misconception="left_to_right_precedence",
                explanation="Sumaste primero 6 + 8 = 14 y luego dividiste entre 2.",
            ),
            "B": DistractorDetail(
                misconception="addition_before_multiplication",
                explanation="Calculaste la división 8 / 2 = 4 pero olvidaste sumar 6.",
            ),
            "D": DistractorDetail(
                misconception="ignored_parentheses",
                explanation="Sumaste 6 + 8 directamente ignorando la división.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_arith_ord_04",
        topic="arithmetic",
        subconcept="order_of_operations",
        question_text="¿Cuánto es 20 - 4 * 3?",
        options={"A": "48", "B": "12", "C": "16", "D": "8"},
        correct_option="D",
        distractors={
            "A": DistractorDetail(
                misconception="left_to_right_precedence",
                explanation="Restaste 20 - 4 = 16 y luego multiplicaste por 3.",
            ),
            "B": DistractorDetail(
                misconception="addition_before_multiplication",
                explanation="Calculaste solo el producto 4 * 3 = 12 sin restar de 20.",
            ),
            "C": DistractorDetail(
                misconception="ignored_parentheses",
                explanation="Restaste solo 4 ignorando el factor multiplicativo 3.",
            ),
        },
    ),
]
