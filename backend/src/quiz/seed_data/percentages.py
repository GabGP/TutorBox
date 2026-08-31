from quiz.contracts.models import DistractorDetail, QuizQuestion

PERCENTAGES_QUESTIONS: list[QuizQuestion] = [
    QuizQuestion(
        id="seed_pct_01",
        topic="decimals_percentages",
        subconcept="percentages",
        question_text="¿Cuál es el 20% de 50?",
        options={"A": "1000", "B": "10", "C": "2.5", "D": "30"},
        correct_option="B",
        distractors={
            "A": DistractorDetail(
                misconception="multiplied_by_percentage_directly",
                explanation="Multiplicaste 50 * 20 sin dividir entre 100.",
            ),
            "C": DistractorDetail(
                misconception="confused_fraction_with_percent",
                explanation="Dividiste 50 / 20 en lugar de calcular el 20%.",
            ),
            "D": DistractorDetail(
                misconception="subtracted_percentage_as_raw_number",
                explanation="Restaste 50 - 20 directamente.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_pct_02",
        topic="decimals_percentages",
        subconcept="percentages",
        question_text="¿Cuál es el 25% de 80?",
        options={"A": "2000", "B": "3.2", "C": "20", "D": "55"},
        correct_option="C",
        distractors={
            "A": DistractorDetail(
                misconception="multiplied_by_percentage_directly",
                explanation="Multiplicaste 80 * 25 sin convertir a centésimas.",
            ),
            "B": DistractorDetail(
                misconception="confused_fraction_with_percent",
                explanation="Dividiste 80 / 25 en vez de calcular el porcentaje.",
            ),
            "D": DistractorDetail(
                misconception="subtracted_percentage_as_raw_number",
                explanation="Restaste 80 - 25 como si fuera un valor absoluto.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_pct_03",
        topic="decimals_percentages",
        subconcept="percentages",
        question_text="¿Cuál es el 10% de 200?",
        options={"A": "2000", "B": "20", "C": "2", "D": "190"},
        correct_option="B",
        distractors={
            "A": DistractorDetail(
                misconception="multiplied_by_percentage_directly",
                explanation="Multiplicaste 200 * 10 omitiendo la división entre 100.",
            ),
            "C": DistractorDetail(
                misconception="confused_fraction_with_percent",
                explanation="Dividiste entre 100 dos veces.",
            ),
            "D": DistractorDetail(
                misconception="subtracted_percentage_as_raw_number",
                explanation="Restaste 200 - 10 directamente.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_pct_04",
        topic="decimals_percentages",
        subconcept="percentages",
        question_text="¿Cuál es el 50% de 60?",
        options={"A": "3000", "B": "1.2", "C": "10", "D": "30"},
        correct_option="D",
        distractors={
            "A": DistractorDetail(
                misconception="multiplied_by_percentage_directly",
                explanation="Multiplicaste 60 * 50 = 3000 sin dividir entre 100.",
            ),
            "B": DistractorDetail(
                misconception="confused_fraction_with_percent",
                explanation="Dividiste 60 / 50 en vez de hallar el 50%.",
            ),
            "C": DistractorDetail(
                misconception="subtracted_percentage_as_raw_number",
                explanation="Restaste 60 - 50 = 10.",
            ),
        },
    ),
    QuizQuestion(
        id="seed_pct_05",
        topic="decimals_percentages",
        subconcept="percentages",
        question_text="¿Cuál es el 75% de 40?",
        options={"A": "30", "B": "3000", "C": "1.875", "D": "35"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="multiplied_by_percentage_directly",
                explanation="Multiplicaste 40 * 75 sin dividir entre 100.",
            ),
            "C": DistractorDetail(
                misconception="confused_fraction_with_percent",
                explanation="Dividiste 75 / 40 en lugar de aplicar el 75%.",
            ),
            "D": DistractorDetail(
                misconception="subtracted_percentage_as_raw_number",
                explanation="Restaste 75 - 40 = 35 directamente en vez de calcular el 75%.",
            ),
        },
    ),
]
