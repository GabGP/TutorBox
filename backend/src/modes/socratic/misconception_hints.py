"""One Socratic question per misconception, aimed at the step that went wrong.

The planner names the misconception behind a wrong answer (telemetry/error_type.py)
and asks the question for it here instead of the next rung of the hint ladder.
Five questions per misconception live in knowledge_base.json, one picked by
the problem; their only numbers are the problem's
own ({p}). Each one is still re-checked with the containment check, and None
sends the planner back to the ladder.
"""

from modes.socratic.containment import leaks
from modes.socratic.knowledge import misconception_question
from modes.socratic.problems import Problem

__all__ = ["misconception_hint"]


def misconception_hint(problem: Problem, slug: str) -> str | None:
    """The question for the misconception; None if it has none or it would leak."""
    template = misconception_question(slug, problem.text)
    if template is None:
        return None
    text = template.format(p=problem.text)
    return None if leaks(text, problem) else text
