from src.quiz.taxonomy import (
    CURRICULUM_TAXONOMY,
    get_available_topics,
    is_valid_subconcept,
    is_valid_topic,
)


def test_taxonomy_structure():
    assert "arithmetic" in CURRICULUM_TAXONOMY
    assert "fractions" in CURRICULUM_TAXONOMY
    assert "pre_algebra" in CURRICULUM_TAXONOMY
    assert "decimals_percentages" in CURRICULUM_TAXONOMY


def test_get_available_topics():
    topics = get_available_topics()
    assert len(topics) >= 4
    topic_names = [t.name for t in topics]
    assert "arithmetic" in topic_names
    assert "pre_algebra" in topic_names

    pre_alg = next(t for t in topics if t.name == "pre_algebra")
    sub_names = [s.name for s in pre_alg.subconcepts]
    assert "two_step_equations" in sub_names


def test_is_valid_topic_and_subconcept():
    assert is_valid_topic("arithmetic") is True
    assert is_valid_topic("quantum_physics") is False

    assert is_valid_subconcept("arithmetic", "order_of_operations") is True
    assert is_valid_subconcept("arithmetic", "calculus_limits") is False
    assert is_valid_subconcept("non_existent_topic", "any_sub") is False
