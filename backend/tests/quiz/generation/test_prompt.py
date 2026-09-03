from quiz.contracts.taxonomy import CURRICULUM_TAXONOMY
from quiz.generation.exemplars import get_canonical_exemplar
from quiz.generation.prompt import (
    build_feedback_prompt,
    build_quiz_response_format,
    build_quiz_system_prompt,
    build_quiz_user_prompt,
)


def test_build_quiz_system_prompt_default():
    prompt = build_quiz_system_prompt()
    assert "TutorBox" in prompt
    assert "strict JSON format" in prompt
    assert "MANDATORY REVERSE-ENGINEERING PROTOCOL" in prompt
    assert "Step 1 (Target Truth)" in prompt
    assert "ANTI-CONTRADICTION RULE" in prompt
    assert '"correct_option"' in prompt
    assert '"distractors"' in prompt
    assert '"misconception"' in prompt
    assert '"explanation"' in prompt
    assert "Spanish" in prompt
    assert "NOVELTY RULE" in prompt
    assert "LaTeX math delimiters" in prompt
    assert "$x$" in prompt
    assert "plain text" in prompt
    assert "explicitly formulate the mathematical equation" in prompt


def test_build_quiz_system_prompt_pre_algebra():
    prompt = build_quiz_system_prompt("pre_algebra")
    assert "MANDATORY PRE-ALGEBRA REVERSE-ENGINEERING PROTOCOL" in prompt
    assert "Step 1 (Target Root)" in prompt
    assert "Step 2 (Coefficients)" in prompt
    assert "Step 3 (Assemble Equation)" in prompt


def test_build_quiz_system_prompt_arithmetic():
    prompt = build_quiz_system_prompt("arithmetic")
    assert "MANDATORY ARITHMETIC REVERSE-ENGINEERING PROTOCOL" in prompt
    assert "Step 1 (Target Value)" in prompt
    assert "precedence" in prompt


def test_build_quiz_user_prompt_with_topic_and_subconcept():
    prompt = build_quiz_user_prompt("arithmetic", "order_of_operations")
    assert "arithmetic" in prompt
    assert "order_of_operations" in prompt
    assert "left_to_right_precedence" in prompt
    assert "Required JSON format" not in prompt
    assert "schema reference ONLY" not in prompt
    assert "2x + 4 = 12" not in prompt
    assert "3 + 4 * 2" not in prompt


def test_build_quiz_user_prompt_pre_algebra_two_step():
    prompt = build_quiz_user_prompt("pre_algebra", "two_step_equations")
    assert "pre_algebra" in prompt
    assert "two_step_equations" in prompt
    assert "divided_before_subtracting" in prompt
    assert "forgot_division" in prompt
    assert "Required JSON format" not in prompt
    assert "2x + 4 = 12" not in prompt


def test_build_quiz_user_prompt_with_topic_only():
    prompt = build_quiz_user_prompt("fractions")
    assert "fractions" in prompt
    assert "added_denominators" in prompt
    assert "Required JSON format" not in prompt
    assert "2x + 4 = 12" not in prompt


def test_build_quiz_user_prompt_with_custom_misconceptions():
    custom = ["custom_error_1", "custom_error_2"]
    prompt = build_quiz_user_prompt(
        "arithmetic", "order_of_operations", recognized_misconceptions=custom
    )
    assert "custom_error_1" in prompt
    assert "custom_error_2" in prompt
    assert "Required JSON format" not in prompt


def test_get_canonical_exemplar_structural_format():
    exemplar = get_canonical_exemplar("arithmetic", "addition_subtraction")
    assert exemplar["topic"] == "arithmetic"
    assert exemplar["subconcept"] == "addition_subtraction"
    assert exemplar["correct_option"] == "A"
    assert set(exemplar["options"].keys()) == {"A", "B", "C", "D"}
    assert set(exemplar["distractors"].keys()) == {"B", "C", "D"}
    for distractor_info in exemplar["distractors"].values():
        assert "misconception" in distractor_info
        assert "explanation" in distractor_info
    assert "[Escribe aquí el enunciado completo" in exemplar["question_text"]


def test_get_canonical_exemplar_defaults():
    default_exemplar = get_canonical_exemplar()
    assert default_exemplar["topic"] == "algebra_formativa"
    assert default_exemplar["subconcept"] == "concepto_general"
    assert len(default_exemplar["options"]) == 4
    assert len(default_exemplar["distractors"]) == 3


def test_build_quiz_user_prompt_unknown_topic():
    prompt = build_quiz_user_prompt("calculus")
    assert "calculus" in prompt
    assert "Required JSON format" not in prompt


def test_build_feedback_prompt():
    base = "Generate 1 diagnostic quiz question for topic 'fractions'."
    errors = [
        "Distractors must contain 3 items.",
        "Option B is missing 'explanation'.",
    ]
    feedback = build_feedback_prompt(base, errors)
    assert base in feedback
    assert "ATTENTION: Your previous response was rejected" in feedback
    assert "CORRECTION INSTRUCTIONS" in feedback
    assert "- Distractors must contain 3 items." in feedback
    assert "- Option B is missing 'explanation'." in feedback
    assert "Ensure 'question_text' explicitly includes" in feedback
    assert "CRITICAL REVISION RULE" in feedback
    assert "backward formulation" in feedback
    assert "DO NOT reuse numbers or computed truth values" in feedback


def test_all_taxonomy_pairs_exemplars_consistent():
    for topic_name, subconcept_dict in CURRICULUM_TAXONOMY.items():
        for subconcept_name in subconcept_dict:
            exemplar = get_canonical_exemplar(topic_name, subconcept_name)
            assert exemplar["topic"] == topic_name
            assert exemplar["subconcept"] == subconcept_name
            assert len(exemplar["options"]) == 4
            assert len(exemplar["distractors"]) == 3
            assert exemplar["correct_option"] in exemplar["options"]
            assert set(exemplar["distractors"].keys()) == {"B", "C", "D"}


def test_build_quiz_response_format():
    fmt = build_quiz_response_format()
    assert fmt["type"] == "json_schema"
    assert "json_schema" in fmt
    schema = fmt["json_schema"]["schema"]
    assert schema["type"] == "object"
    assert "topic" in schema["properties"]
    assert "subconcept" in schema["properties"]
    assert "question_text" in schema["properties"]
    assert "description" in schema["properties"]["question_text"]
    assert "options" in schema["properties"]
    assert "correct_option" in schema["properties"]
    assert "distractors" in schema["properties"]
    assert schema["properties"]["correct_option"]["enum"] == ["A", "B", "C", "D"]
    assert schema["properties"]["options"]["required"] == ["A", "B", "C", "D"]
    assert set(schema["properties"]["distractors"]["properties"].keys()) == {
        "A",
        "B",
        "C",
        "D",
    }
    assert schema["required"] == [
        "topic",
        "subconcept",
        "question_text",
        "options",
        "correct_option",
        "distractors",
    ]
    assert schema["additionalProperties"] is False
