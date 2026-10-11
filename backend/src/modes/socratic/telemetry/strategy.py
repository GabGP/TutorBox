"""The scaffolding strategy that a tutor turn applies, as the telemetry names it.

A hint's strategy depends on its rung of the hint ladder (0 to 3, bounded by the
planner); every other move's strategy depends only on its kind. A kind that is
not named here is "other", so a move the tutor adds later cannot crash logging.
"""

__all__ = ["STRATEGIES", "scaffolding_strategy"]

_OTHER = "other"
_LADDER_STRATEGIES: dict[int, str] = {
    0: "restate_goal",
    1: "concept_clue",
    2: "smaller_step",
    3: "worked_example",
}
_KIND_STRATEGIES: dict[str, str] = {
    "praise": "confirm_solution",
    "explain": "concept_explanation",
    "think": "think_first",
    "word_problem": "ask_for_operation",
    "show_work": "ask_to_show_work",
    "idea": "acknowledge_idea",
    "social": "social",
    "input": "redirect",
    "beyond": "redirect",
    "negative": "redirect",
    "off_topic": "redirect",
    "orphan": "redirect",
}
STRATEGIES = frozenset(
    {*_LADDER_STRATEGIES.values(), *_KIND_STRATEGIES.values(), _OTHER}
)


def scaffolding_strategy(kind: str, hint_level: int) -> str:
    """The strategy of a move; hint_level is read only for a hint."""
    if kind == "hint":
        return _LADDER_STRATEGIES[hint_level]
    return _KIND_STRATEGIES.get(kind, _OTHER)
