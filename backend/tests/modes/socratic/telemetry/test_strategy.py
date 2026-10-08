"""Scaffolding strategies of tutor turns (modes/socratic/telemetry/strategy.py)."""

import re
from pathlib import Path

import pytest

from modes.socratic import planner
from modes.socratic.telemetry.strategy import STRATEGIES, scaffolding_strategy

PLANNER_SOURCE = Path(planner.__file__)
# A Move call may break its line after the "(", as _judge does.
MOVE_KIND = re.compile(r'Move\(\s*"([a-z_]+)"')
HINT_LADDER = [
    (0, "restate_goal"),
    (1, "concept_clue"),
    (2, "smaller_step"),
    (3, "worked_example"),
]
NON_HINT_KINDS = [
    ("praise", "confirm_solution"),
    ("explain", "concept_explanation"),
    ("think", "think_first"),
    ("word_problem", "ask_for_operation"),
    ("show_work", "ask_to_show_work"),
    ("idea", "acknowledge_idea"),
    ("social", "social"),
    ("input", "redirect"),
    ("beyond", "redirect"),
    ("negative", "redirect"),
    ("off_topic", "redirect"),
    ("orphan", "redirect"),
]


@pytest.mark.parametrize(("hint_level", "strategy"), HINT_LADDER)
def test_each_rung_of_the_hint_ladder_has_its_own_strategy(hint_level, strategy):
    assert scaffolding_strategy("hint", hint_level) == strategy


@pytest.mark.parametrize(("kind", "strategy"), NON_HINT_KINDS)
def test_each_non_hint_kind_has_its_strategy(kind, strategy):
    assert scaffolding_strategy(kind, 0) == strategy


def test_every_kind_the_planner_can_emit_has_a_named_strategy():
    kinds = set(MOVE_KIND.findall(PLANNER_SOURCE.read_text(encoding="utf-8")))

    assert kinds
    assert "hint" in kinds
    assert all(scaffolding_strategy(kind, 0) != "other" for kind in kinds)


def test_an_unknown_kind_is_logged_as_other():
    assert scaffolding_strategy("a_future_move", 0) == "other"


def test_the_public_set_holds_exactly_the_strategies_the_function_returns():
    returned = {scaffolding_strategy("hint", level) for level, _ in HINT_LADDER}
    returned |= {scaffolding_strategy(kind, 0) for kind, _ in NON_HINT_KINDS}
    returned.add(scaffolding_strategy("a_future_move", 0))

    assert returned == STRATEGIES
