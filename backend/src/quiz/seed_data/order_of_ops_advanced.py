from quiz.contracts.models import DistractorDetail, QuizQuestion

ORDER_OF_OPS_ADVANCED_QUESTIONS: list[QuizQuestion] = [
    QuizQuestion(
        id="seed_arith_ord_05",
        topic="arithmetic",
        subconcept="order_of_operations",
        question_text="¿Cuánto es 2 + 3 * 4 + 1?",
        options={"A": "15", "B": "21", "C": "25", "D": "24"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="left_to_right_precedence",
                explanation="Evaluaste en orden estricto de izquierda a derecha.",
            ),
            "C": DistractorDetail(
                misconception="addition_before_multiplication",
                explanation="Hiciste las sumas primero: (2+3) * (4+1) = 25.",
            ),
            "D": DistractorDetail(
                misconception="ignored_parentheses",
                explanation="Multiplicaste 2 * 3 * 4 ignorando las sumas.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_arith_ord_06",
        topic="arithmetic",
        subconcept="order_of_operations",
        question_text="¿Cuánto es 15 - 3 * 2 + 4?",
        options={"A": "28", "B": "13", "C": "5", "D": "20"},
        correct_option="B",
        distractors={
            "A": DistractorDetail(
                misconception="left_to_right_precedence",
                explanation="Calculaste de izquierda a derecha: (15-3)*2 + 4 = 28.",
            ),
            "C": DistractorDetail(
                misconception="addition_before_multiplication",
                explanation="Sumaste antes de restar: 15 - (6 + 4) = 5.",
            ),
            "D": DistractorDetail(
                misconception="ignored_parentheses",
                explanation="No aplicaste la precedencia correcta al producto.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_arith_ord_07",
        topic="arithmetic",
        subconcept="order_of_operations",
        question_text="¿Cuánto es 4 * 3 + 2 * 5?",
        options={"A": "70", "B": "100", "C": "22", "D": "35"},
        correct_option="C",
        distractors={
            "A": DistractorDetail(
                misconception="left_to_right_precedence",
                explanation="Hiciste (4*3 + 2) * 5 = 70 de izquierda a derecha.",
            ),
            "B": DistractorDetail(
                misconception="addition_before_multiplication",
                explanation="Sumaste primero 3 + 2 = 5 y luego multiplicaste 4 * 5 * 5 = 100.",
            ),
            "D": DistractorDetail(
                misconception="ignored_parentheses",
                explanation="Alteraste el orden de los factores de multiplicación.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_arith_ord_08",
        topic="arithmetic",
        subconcept="order_of_operations",
        question_text="¿Cuánto es 18 - 6 / 2?",
        options={"A": "6", "B": "9", "C": "12", "D": "15"},
        correct_option="D",
        distractors={
            "A": DistractorDetail(
                misconception="left_to_right_precedence",
                explanation="Restaste primero 18 - 6 = 12 y luego dividiste entre 2 = 6.",
            ),
            "B": DistractorDetail(
                misconception="addition_before_multiplication",
                explanation="Dividiste 18 / 2 = 9 ignorando la resta de 6.",
            ),
            "C": DistractorDetail(
                misconception="ignored_parentheses",
                explanation="Restaste 18 - 6 ignorando la división.",
            ),
        },
    ),
]
