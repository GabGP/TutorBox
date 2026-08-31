from src.quiz.prompt import (
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


def test_build_quiz_user_prompt_with_topic_only():
    prompt = build_quiz_user_prompt("fractions")
    assert "fractions" in prompt
    assert "added_denominators" in prompt


def test_build_quiz_user_prompt_with_custom_misconceptions():
    custom = ["custom_error_1", "custom_error_2"]
    prompt = build_quiz_user_prompt("geometry", recognized_misconceptions=custom)
    assert "geometry" in prompt
    assert "custom_error_1, custom_error_2" in prompt


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
