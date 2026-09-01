from src.quiz.contracts.taxonomy import CURRICULUM_TAXONOMY
from src.quiz.generation.exemplars import get_canonical_exemplar
from src.quiz.generation.prompt import (
    build_feedback_prompt,
    build_quiz_system_prompt,
    build_quiz_user_prompt,
)


def test_build_quiz_system_prompt():
    prompt = build_quiz_system_prompt()
    assert "TutorBox" in prompt
    assert "strict JSON format" in prompt
    assert '"correct_option"' in prompt
    assert '"distractors"' in prompt
    assert '"misconception"' in prompt
    assert '"explanation"' in prompt
    assert "Spanish" in prompt


def test_build_quiz_user_prompt_with_topic_and_subconcept():
    prompt = build_quiz_user_prompt("arithmetic", "order_of_operations")
    assert "arithmetic" in prompt
    assert "order_of_operations" in prompt
    assert "left_to_right_precedence" in prompt
    assert "Required JSON format" in prompt


def test_build_quiz_user_prompt_pre_algebra_two_step():
    prompt = build_quiz_user_prompt("pre_algebra", "two_step_equations")
    assert "pre_algebra" in prompt
    assert "two_step_equations" in prompt
    assert "2*x + 4 = 12" in prompt
    assert "divided_before_subtracting" in prompt
    assert "forgot_division" in prompt


def test_build_quiz_user_prompt_with_topic_only():
    prompt = build_quiz_user_prompt("fractions")
    assert "fractions" in prompt
    assert "added_denominators" in prompt


def test_build_quiz_user_prompt_with_custom_misconceptions():
    custom = ["custom_error_1", "custom_error_2"]
    prompt = build_quiz_user_prompt(
        "arithmetic", "order_of_operations", recognized_misconceptions=custom
    )
    assert "custom_error_1" in prompt
    assert "custom_error_2" in prompt


def test_get_canonical_exemplar_unknown_topic_fallback():
    exemplar_fallback = get_canonical_exemplar("unknown_topic", "unknown_subconcept")
    assert exemplar_fallback["topic"] == "unknown_topic"
    assert "unknown_topic" in exemplar_fallback["question_text"]
    assert "3 + 4 * 2" not in exemplar_fallback["question_text"]

    exemplar_topic_match = get_canonical_exemplar(
        "arithmetic", "nonexistent_subconcept"
    )
    assert exemplar_topic_match["topic"] == "arithmetic"


def test_build_quiz_user_prompt_unknown_topic():
    prompt = build_quiz_user_prompt("calculus")
    assert "calculus" in prompt
    assert "Required JSON format" in prompt


def test_build_feedback_prompt():
    base = "Generate 1 diagnostic quiz question for topic 'fractions'."
    errors = [
        "Distractors must contain 3 items.",
        "Option B is missing 'explanation'.",
    ]
    feedback = build_feedback_prompt(base, errors)
    assert base in feedback
    assert "ATTENTION: Your previous response was rejected" in feedback
    assert "- Distractors must contain 3 items." in feedback
    assert "- Option B is missing 'explanation'." in feedback


def test_all_taxonomy_pairs_have_canonical_exemplars():
    for topic_name, subconcept_dict in CURRICULUM_TAXONOMY.items():
        for subconcept_name in subconcept_dict:
            exemplar = get_canonical_exemplar(topic_name, subconcept_name)
            assert exemplar["topic"] == topic_name
            assert exemplar["subconcept"] == subconcept_name
            assert len(exemplar["options"]) == 4
            assert len(exemplar["distractors"]) == 3
            for distractor_info in exemplar["distractors"].values():
                assert (
                    distractor_info["misconception"] in subconcept_dict[subconcept_name]
                )


def test_get_canonical_exemplar_fallbacks():
    generic_arithmetic = get_canonical_exemplar("arithmetic", None)
    assert generic_arithmetic["topic"] == "arithmetic"

    unknown_topic = get_canonical_exemplar("unknown_topic", "unknown_subconcept")
    assert unknown_topic["topic"] == "unknown_topic"
    assert unknown_topic["subconcept"] == "unknown_subconcept"
