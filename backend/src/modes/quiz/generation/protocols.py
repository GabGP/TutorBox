"""Pedagogical derivation protocols for topic-adaptive SLM prompt engineering."""

_PRE_ALGEBRA_PROTOCOL = (
    "MANDATORY PRE-ALGEBRA REVERSE-ENGINEERING PROTOCOL:\n"
    "Step 1 (Target Root): Choose an integer root value for your chosen variable "
    "(non-zero integer).\n"
    "Step 2 (Coefficients): Choose non-zero integer coefficients for the variable "
    "and constant term, selecting signs (+ or -) and variable symbol freely.\n"
    "Step 3 (Assemble Equation): Multiply the variable coefficient by the root value, "
    "then add the constant term to compute the equality constant. Formulate the equation "
    "using these components.\n"
    "Step 4 (Distractor Derivations): For each distractor misconception, apply that "
    "specific erroneous operation to derive a distinct numeric outcome.\n"
    "Step 5 (Binding): Place the true solution and the 3 derived distractor results "
    "across options A through D."
)

_PRE_ALGEBRA_ONE_STEP_PROTOCOL = (
    "MANDATORY ONE-STEP EQUATION PROTOCOL:\n"
    "Step 1 (Target Root): Choose a non-zero integer solution x in [-20, 20].\n"
    "Step 2 (Single Operation Form): Create EXACTLY ONE of these forms:\n"
    "  - Addition/Subtraction: x + b = c or x - b = c (variable coefficient is 1 or -1).\n"
    "  - Multiplication: ax = c where a is a non-zero integer and constant term is 0.\n"
    "  - Division: x/a = c where a is a non-zero integer and constant term is 0.\n"
    "FORBIDDEN: NEVER write ax + b = c with BOTH a non-trivial coefficient AND a "
    "non-zero constant. That is a 2-step equation.\n"
    "Step 3 (Assemble): Compute the equality constant from your root and chosen form.\n"
    "Step 4 (Distractor Derivations): For each distractor, apply a specific erroneous "
    "operation to derive a distinct numeric outcome.\n"
    "Step 5 (Binding): Place the true solution and 3 distractor results across A-D."
)

_PRE_ALGEBRA_TWO_STEP_PROTOCOL = (
    "MANDATORY TWO-STEP EQUATION PROTOCOL:\n"
    "Step 1 (Target Root): Choose a non-zero integer solution x in [-20, 20].\n"
    "Step 2 (Coefficients): Choose a non-trivial integer coefficient a (not 0, 1, or -1) "
    "AND a non-zero integer constant term b to form ax + b = c.\n"
    "Step 3 (Assemble Equation): Compute c = a*x + b. Formulate the equation.\n"
    "Step 4 (Distractor Derivations): For each distractor misconception, apply that "
    "specific erroneous operation to derive a distinct numeric outcome.\n"
    "Step 5 (Binding): Place the true solution and 3 distractor results across A-D."
)

_PRE_ALGEBRA_SUBCONCEPT_PROTOCOLS: dict[str, str] = {
    "one_step_equations": _PRE_ALGEBRA_ONE_STEP_PROTOCOL,
    "two_step_equations": _PRE_ALGEBRA_TWO_STEP_PROTOCOL,
}

_ARITHMETIC_PROTOCOL = (
    "MANDATORY ARITHMETIC REVERSE-ENGINEERING PROTOCOL:\n"
    "Step 1 (Target Value): Choose an integer target solution with certainty.\n"
    "Step 2 (Construct Expression): Build an arithmetic expression with multiple "
    "operations or regrouping that evaluates strictly to your target solution.\n"
    "Step 3 (Distractor Derivations): For each distractor misconception (such as precedence "
    "confusion, carry/borrow error, or operation inversion), compute the exact erroneous result.\n"
    "Step 4 (Binding): Place the true solution and the 3 derived distractor results "
    "across options A through D."
)

_FRACTIONS_PROTOCOL = (
    "MANDATORY FRACTIONS REVERSE-ENGINEERING PROTOCOL:\n"
    "Step 1 (Target Fraction): Choose a clean, simplified fraction or integer target solution.\n"
    "Step 2 (Construct Problem): Build a fraction operation (addition, subtraction, "
    "multiplication, division, or simplification) that strictly evaluates to this target solution.\n"
    "Step 3 (Distractor Derivations): For each distractor misconception (such as adding "
    "denominators directly, ignoring LCD, or inverted divisor errors), compute the distinct "
    "erroneous fraction.\n"
    "Step 4 (Binding): Place the true solution and the 3 derived distractor results "
    "across options A through D."
)

_DECIMALS_PERCENTAGES_PROTOCOL = (
    "MANDATORY DECIMALS & PERCENTAGES REVERSE-ENGINEERING PROTOCOL:\n"
    "Step 1 (Target Value): Choose a clean decimal, integer, or percentage target solution.\n"
    "Step 2 (Construct Problem): Build a decimal arithmetic or percentage problem "
    "that strictly evaluates to this target solution.\n"
    "Step 3 (Distractor Derivations): For each distractor misconception (such as misplaced "
    "decimal point, raw percent multiplication, or unaligned decimals), compute the distinct "
    "erroneous outcome.\n"
    "Step 4 (Binding): Place the true solution and the 3 derived distractor results "
    "across options A through D."
)

_UNIVERSAL_PROTOCOL = (
    "MANDATORY REVERSE-ENGINEERING PROTOCOL:\n"
    "Step 1 (Target Truth): Choose the exact, final mathematical answer first with "
    "certainty (clean integer or simplified fraction/decimal).\n"
    "Step 2 (Construct Problem): Formulate the equation, arithmetic expression, or "
    "fraction problem that strictly evaluates to your target solution.\n"
    "Step 3 (Distractor Derivations): For each distractor misconception, apply that "
    "specific erroneous operation or rule to derive a distinct numeric outcome.\n"
    "Step 4 (Binding): Place the true solution and the 3 derived distractor results "
    "across options A through D."
)

_TOPIC_PROTOCOLS: dict[str, str] = {
    "pre_algebra": _PRE_ALGEBRA_PROTOCOL,
    "arithmetic": _ARITHMETIC_PROTOCOL,
    "fractions": _FRACTIONS_PROTOCOL,
    "decimals_percentages": _DECIMALS_PERCENTAGES_PROTOCOL,
}


def get_derivation_protocol(
    topic: str | None = None,
    subconcept: str | None = None,
) -> str:
    """Returns the topic-specific reverse-engineering cognitive derivation protocol.

    When *topic* is ``"pre_algebra"`` and a recognized *subconcept* is
    provided (``"one_step_equations"`` or ``"two_step_equations"``), a
    subconcept-specific protocol is returned.  Unknown subconcepts
    gracefully fall back to the generic pre-algebra protocol.
    """
    if topic == "pre_algebra" and subconcept:
        return _PRE_ALGEBRA_SUBCONCEPT_PROTOCOLS.get(subconcept, _PRE_ALGEBRA_PROTOCOL)
    if topic and topic in _TOPIC_PROTOCOLS:
        return _TOPIC_PROTOCOLS[topic]
    return _UNIVERSAL_PROTOCOL


ONE_STEP_RECOVERY_INSTRUCTION: str = (
    "STRUCTURAL FIX: For 'one_step_equations', formulate an equation with EXACTLY "
    "1 operation (e.g. x + 5 = 12, 3x = 15, or x/3 = 5). "
    "NEVER write 2-step equations like 2x + 6 = 10."
)


def get_structural_recovery_instruction(errors: list[str]) -> str:
    """Returns targeted structural recovery guidance if validation errors indicate mismatch."""
    has_pedagogical_mismatch = any(
        "Pedagogical mismatch" in err or "1-step equation" in err for err in errors
    )
    return f"\n{ONE_STEP_RECOVERY_INSTRUCTION}" if has_pedagogical_mismatch else ""
