from quiz.contracts.models import DistractorDetail, QuizQuestion

DECIMALS_QUESTIONS: list[QuizQuestion] = [
    QuizQuestion(
        id="seed_dec_01",
        topic="decimals_percentages",
        subconcept="decimal_operations",
        question_text="¿Cuánto es 3.5 + 2.15?",
        options={"A": "5.65", "B": "5.20", "C": "56.5", "D": "2.50"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="ignored_decimal_places",
                explanation="Sumaste 5 + 15 ignorando el valor posicional de las décimas.",
            ),
            "C": DistractorDetail(
                misconception="misplaced_decimal_point",
                explanation="Colocaste el punto decimal una posición a la derecha.",
            ),
            "D": DistractorDetail(
                misconception="added_without_aligning_decimal",
                explanation="Alineaste los dígitos al extremo derecho sin alinear la coma.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_dec_02",
        topic="decimals_percentages",
        subconcept="decimal_operations",
        question_text="¿Cuánto es 7.8 - 3.25?",
        options={"A": "4.60", "B": "4.55", "C": "45.5", "D": "3.45"},
        correct_option="B",
        distractors={
            "A": DistractorDetail(
                misconception="ignored_decimal_places",
                explanation="No agregaste un cero al 7.80 para restar 25 centésimas adecuadamente.",
            ),
            "C": DistractorDetail(
                misconception="misplaced_decimal_point",
                explanation="Ubicaste incorrectamente el punto decimal en la diferencia.",
            ),
            "D": DistractorDetail(
                misconception="added_without_aligning_decimal",
                explanation="Desalineaste las columnas posicionales durante la resta.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_dec_03",
        topic="decimals_percentages",
        subconcept="decimal_operations",
        question_text="¿Cuánto es 1.2 * 4.0?",
        options={"A": "48", "B": "4.2", "C": "4.8", "D": "0.48"},
        correct_option="C",
        distractors={
            "A": DistractorDetail(
                misconception="misplaced_decimal_point",
                explanation="Olvidaste colocar el punto decimal en el producto final.",
            ),
            "B": DistractorDetail(
                misconception="ignored_decimal_places",
                explanation="Multiplicaste solo la parte entera.",
            ),
            "D": DistractorDetail(
                misconception="added_without_aligning_decimal",
                explanation="Recorriste el punto decimal lugares de más a la izquierda.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_dec_04",
        topic="decimals_percentages",
        subconcept="decimal_operations",
        question_text="¿Cuánto es 6.4 / 2.0?",
        options={"A": "32", "B": "3.0", "C": "0.32", "D": "3.2"},
        correct_option="D",
        distractors={
            "A": DistractorDetail(
                misconception="misplaced_decimal_point",
                explanation="Omitiste el punto decimal en el cociente.",
            ),
            "B": DistractorDetail(
                misconception="ignored_decimal_places",
                explanation="Dividiste solo la parte entera ignorando 0.4.",
            ),
            "C": DistractorDetail(
                misconception="added_without_aligning_decimal",
                explanation="Desplazaste el punto una posición de más a la izquierda.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_dec_05",
        topic="decimals_percentages",
        subconcept="decimal_operations",
        question_text="¿Cuánto es 4.25 + 1.5?",
        options={"A": "5.75", "B": "5.30", "C": "57.5", "D": "4.40"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="ignored_decimal_places",
                explanation="Sumaste 25 + 5 como 30 en vez de sumar 5 décimas a 2 décimas.",
            ),
            "C": DistractorDetail(
                misconception="misplaced_decimal_point",
                explanation="Colocaste mal el separador decimal.",
            ),
            "D": DistractorDetail(
                misconception="added_without_aligning_decimal",
                explanation="Sumaste los números sin alinear la coma decimal.",
            ),
        },
    ),
]
