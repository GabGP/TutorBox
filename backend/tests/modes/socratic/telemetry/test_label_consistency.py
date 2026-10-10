"""The labels agree with each other: a misconception belongs to its problem's concept.

The rows are the ones the error-type tests already prove, so a rule and the
taxonomy cannot drift apart without a test failing.
"""

import pytest

from modes.quiz.contracts.taxonomy import CURRICULUM_TAXONOMY
from modes.socratic import telemetry
from modes.socratic.problems import find_problem
from modes.socratic.telemetry import concept, error_type, strategy
from tests.conftest import required
from tests.modes.socratic.telemetry.test_error_type import LABELLED, RULE_ORDER

# Every name the package exports, with the object its own module defines.
PACKAGE_EXPORTS = [
    ("Concept", concept.Concept),
    ("concept_for", concept.concept_for),
    ("STRATEGIES", strategy.STRATEGIES),
    ("scaffolding_strategy", strategy.scaffolding_strategy),
    ("ERROR_SLUGS", error_type.ERROR_SLUGS),
    ("UNCLASSIFIED", error_type.UNCLASSIFIED),
    ("classify_error", error_type.classify_error),
]
# (problem as the child typed it, the misconception the tests label it with)
MISCONCEPTION_ROWS = [(text, slug) for text, _attempt, slug in LABELLED + RULE_ORDER]


def test_the_package_exports_exactly_the_telemetry_names():
    assert sorted(telemetry.__all__) == sorted(name for name, _ in PACKAGE_EXPORTS)


@pytest.mark.parametrize(("name", "origin"), PACKAGE_EXPORTS)
def test_each_exported_name_is_importable_from_the_package(name, origin):
    assert getattr(telemetry, name) is origin


@pytest.mark.parametrize(("text", "slug"), MISCONCEPTION_ROWS)
def test_a_misconception_is_listed_under_the_concept_of_its_problem(text, slug):
    problem = find_problem(text)
    assert problem is not None, text
    label = concept.concept_for(problem, None)

    topic, subconcept = required(label.topic), required(label.subconcept)
    assert slug in CURRICULUM_TAXONOMY[topic][subconcept]
