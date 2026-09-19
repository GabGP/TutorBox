# Question Pool Authoring Brief

<div align="center">

| 🏠 [TutorBox](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 [Docs](../README.md) › **Quiz** › **Question Pool Brief** • **Related:** [Diagnostic Distractors](../architecture/diagnostic-distractors.md) • [Quiz API](../api/quiz.md) • [Three Modes](../architecture/three-modes.md)

</div>

---

This brief is self-contained: paste it (or sections 2–8 plus the prompt in section 10) into a chat with a frontier model that has **no repository access**, and the questions it returns will pass `backend/tests/modes/quiz/seed_data/test_pool.py` unchanged. Every rule below is derived from the validator source and cites the file that enforces it.

## Table of Contents
- [1. Purpose](#1-purpose)
- [2. JSON contract](#2-json-contract)
- [3. Taxonomy](#3-taxonomy)
- [4. What SymPy can verify](#4-what-sympy-can-verify)
- [5. Per-subconcept structural rules](#5-per-subconcept-structural-rules)
- [6. Distractor explanation rules](#6-distractor-explanation-rules)
- [7. Pedagogy & style](#7-pedagogy--style)
- [8. Exemplars](#8-exemplars)
- [9. Batch plan](#9-batch-plan)
- [10. The generation prompt](#10-the-generation-prompt)

---

## 1. Purpose

Classroom Quiz mode (primary school, Spanish): the teacher launches a question, students vote A–D, and when **>51%** of voters pick the same distractor the appliance speaks that distractor's `explanation` aloud through offline TTS. This pool of pre-verified questions replaces on-device SLM generation, so each question must pass the same deterministic validators the SLM path runs.

---

## 2. JSON contract

Canonical schema — `backend/schemas/v1/quiz_question.schema.json`, verbatim:

```json
{
  "$defs": {
    "DistractorDetail": {
      "properties": {
        "misconception": {
          "description": "Slug of the diagnosed misconception",
          "maxLength": 100,
          "minLength": 2,
          "title": "Misconception",
          "type": "string"
        },
        "explanation": {
          "description": "Primary-school friendly explanation",
          "maxLength": 500,
          "minLength": 5,
          "title": "Explanation",
          "type": "string"
        }
      },
      "required": [
        "misconception",
        "explanation"
      ],
      "title": "DistractorDetail",
      "type": "object"
    }
  },
  "properties": {
    "schema_version": {
      "default": "1.0.0",
      "description": "Contract schema version",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "title": "Schema Version",
      "type": "string"
    },
    "topic": {
      "maxLength": 64,
      "minLength": 2,
      "title": "Topic",
      "type": "string"
    },
    "subconcept": {
      "maxLength": 64,
      "minLength": 2,
      "title": "Subconcept",
      "type": "string"
    },
    "question_text": {
      "maxLength": 500,
      "minLength": 5,
      "title": "Question Text",
      "type": "string"
    },
    "options": {
      "additionalProperties": {
        "type": "string"
      },
      "title": "Options",
      "type": "object"
    },
    "correct_option": {
      "enum": [
        "A",
        "B",
        "C",
        "D"
      ],
      "title": "Correct Option",
      "type": "string"
    },
    "distractors": {
      "additionalProperties": {
        "$ref": "#/$defs/DistractorDetail"
      },
      "title": "Distractors",
      "type": "object"
    },
    "id": {
      "maxLength": 64,
      "minLength": 1,
      "title": "Id",
      "type": "string"
    }
  },
  "required": [
    "topic",
    "subconcept",
    "question_text",
    "options",
    "correct_option",
    "distractors",
    "id"
  ],
  "title": "QuizQuestion",
  "type": "object",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://tutorbox.local/schemas/v1/quiz_question.schema.json",
  "version": "1.0.0",
  "description": "Canonical versioned contract schema for TutorBox diagnostic multiple-choice quiz questions."
}
```

Field limits enforced by `backend/src/modes/quiz/contracts/models.py` (`QuizQuestion`):

| Field | Rule | Source line |
| :--- | :--- | :--- |
| `id` | string, 1–64 chars, required | `models.py` L91 |
| `schema_version` | write `"1.0.0"` explicitly (default) | L42–46 |
| `topic`, `subconcept` | 2–64 chars, exact English slugs from section 3 | L47–48 |
| `question_text` | 5–500 chars | L49 |
| `options` | object with **exactly** keys `A`,`B`,`C`,`D`; every value non-blank | L66–74 |
| `correct_option` | one of `"A"`,`"B"`,`"C"`,`"D"` | L51 |
| `distractors` | object keyed by **exactly the 3 non-correct letters**, nothing else | L76–82 |
| `distractors.*.misconception` | 2–100 chars, a slug from section 3 | L12–17 |
| `distractors.*.explanation` | 5–500 chars (and ≥10 after trimming, section 6) | L18–23 |

**Id convention:** `pool_<topic>_<subconcept>_<NNN>` with `NNN` zero-padded to 3 digits (`pool_arithmetic_addition_subtraction_001`), unique across the whole pool. The checker rejects any other shape (`test_pool.py::test_pool_ids_are_unique_and_follow_convention`).

---

## 3. Taxonomy

`backend/src/modes/quiz/contracts/taxonomy.py`, verbatim:

```python
CURRICULUM_TAXONOMY: dict[str, dict[str, list[str]]] = {
    "arithmetic": {
        "addition_subtraction": [
            "sign_error",
            "borrowing_error",
            "alignment_error",
            "added_instead_of_subtracted",
        ],
        "multiplication_division": [
            "table_lookup_error",
            "remainder_ignored",
            "inverted_division",
            "forgot_carry",
        ],
        "order_of_operations": [
            "left_to_right_precedence",
            "addition_before_multiplication",
            "ignored_parentheses",
        ],
    },
    "fractions": {
        "addition_subtraction": [
            "added_denominators",
            "ignored_common_denominator",
            "subtracted_denominators",
        ],
        "multiplication_division": [
            "cross_multiplied_for_product",
            "forgot_to_invert_divisor",
            "multiplied_only_numerators",
        ],
        "simplification": [
            "divided_only_numerator",
            "subtracted_to_reduce",
            "partial_factor_division",
        ],
    },
    "pre_algebra": {
        "one_step_equations": [
            "sign_flip_error",
            "wrong_inverse_operation",
            "applied_op_to_one_side_only",
        ],
        "two_step_equations": [
            "divided_before_subtracting",
            "forgot_division",
            "subtracted_instead_of_divided",
            "sign_inversion_error",
        ],
    },
    "decimals_percentages": {
        "decimal_operations": [
            "misplaced_decimal_point",
            "ignored_decimal_places",
            "added_without_aligning_decimal",
        ],
        "percentages": [
            "multiplied_by_percentage_directly",
            "confused_fraction_with_percent",
            "subtracted_percentage_as_raw_number",
        ],
    },
}
```

Rules (`backend/src/modes/quiz/validation/taxonomy_validator.py`):

- `topic` and `subconcept` must equal the ones the file is named for (L26–36) and the subconcept must exist under that topic (L38–47).
- Every `misconception` must be one of the slugs listed under **that exact topic/subconcept** (L49–51, L69–75). A slug from a sibling subconcept is rejected, e.g. `sign_error` on a `two_step_equations` question.
- The 3 distractors of one question use **3 different slugs** (enforced by the pool checker, `test_pool.py::_validate_entry`, because the >51% rule speaks one explanation per option — two options mapping to the same misconception would be indistinguishable in the teacher report).

---

## 4. What SymPy can verify

`SymPyMathValidator` (`backend/src/modes/quiz/validation/validator.py`) computes the truth from `question_text` alone, then checks that the correct option equals it and that **no** distractor does. If it cannot derive a truth the question is rejected with *"No verifiable math"* (L84–88). Truth extraction is `extract_and_solve_problem` in `backend/src/core/math_engine/parser.py` (L87–109):

**Pre-normalization (L89–98):** `¿` and `?` are deleted; `÷`→`/`, `×`→`*`, `·`→`*`; a comma between digits becomes a decimal point (`2,5`→`2.5`); a colon between digits becomes division (`12 : 4`→`12/4`). Nothing else is stripped, so keep other punctuation away from the expression.

**Three evaluation modes, tried in this order** — the first one that yields a value wins:

1. **percentage** (`evaluate_percentage_expression`, L74–84) — regex `(\d+(?:\.\d+)?)\s*%\s*(?:de|\*)\s*(\d+(?:\.\d+)?)`. Truth = N/100 × M (integer if whole).
   Example: `¿Cuál es el 20% de 50?` → `10`.
2. **equation** (`solve_linear_equation`, L45–55, via `equation_parser.py` L30–65) — the **first** `... = ...` whose two sides contain only `0-9 a-z A-Z space + - * / ( ) ^`. Words to the left are stripped token by token until the remainder parses; `2x` becomes `2*x`; the variable is the first letter found; solved with `sympy.solve`, first solution taken.
   Example: `¿Cuál es el valor de x en: 2*x + 4 = 12?` → `4`.
3. **arithmetic** (`evaluate_arithmetic_expression`, L58–71) — the **first** run of text matching `[\d\(\)][\d\s\+\-\*/\(\)\.\^]+[\d\)]` that SymPy can evaluate (`2(3 + 4)` is accepted as `2*(3 + 4)`).
   Example: `¿Cuánto es 12 + 7?` → `19`.

**Consequences (all verified against the code):**

- `question_text` contains **exactly one** explicit expression and **no other digits anywhere**. A stray number in prose is either parsed instead of your expression or, in arithmetic topics, makes the matched span contain letters and fail the structural check (`ast_arithmetic.py` L18–23). `¿Cuánto es 12 + 7 en total si hay 3 grupos?` is rejected; `¿Cuánto es 12 + 7?` passes.
- **No word problems without the bare expression.** `Ana tiene 5 manzanas y compra 3 más. ¿Cuántas tiene?` yields no expression → rejected.
- **Exactly one `=`** in equation questions; two equations in one text fail to parse.
- **No LaTeX.** `$...$`, `\(...\)`, `\[...\]` and `\frac{a}{b}` are silently stripped by `contracts/sanitizer.py` (`strip_math_delimiters`, L32–53), but `\times`, `\cdot`, `\div` survive as letters and break parsing. Write plain text: `+ - * / ( )`. `×`, `÷`, `·` and `:` are accepted but `*` and `/` match the seeds.
- Commas in numbers are normalized (`2,5` = `2.5`) — but write decimals with a dot to match the seeds.
- Fraction division needs parentheses: `(3/4) / (1/2)` → `3/2`; `3/4 / 1/2` is evaluated left-to-right as `3/8`.
- **Options are parsed as values** (`parse_option_expression`, `parser.py` L15–27): an integer, a decimal, a fraction `a/b`, a negative with an ASCII hyphen, or `x = n` (only the number after `=` is kept). Anything else parses to *nothing* — a correct option that cannot be parsed never equals the truth. Rejected forms: `5%`, `3 manzanas`, mixed numbers `1 1/2`, Unicode minus `−3`.
- **Numerically equal values are duplicates** (`are_values_equivalent`, tolerance 1e-6, L30–42; duplicate check `validator.py` L28–54): `2/4` = `1/2` = `0.5` = `0,5`. So no distractor may equal the correct answer or another distractor in *value*. In particular the **unsimplified form of the answer is forbidden as a distractor** (`2/4` next to correct `1/2` fails twice: *Duplicate option values* and *Distractor equals the correct solution*).
- Copy the seed phrasings — they are known to parse:
  - `¿Cuánto es 12 + 7?`
  - `¿Cuál es el valor de x en: 2*x + 4 = 12?`
  - `¿Cuál es el 20% de 50?`
  - `¿Cuánto es 4/8 simplificado?`

---

## 5. Per-subconcept structural rules

`validate_math_structure` (`backend/src/core/math_engine/ast_inspector.py` L13–27) dispatches by topic. `eval_mode` is the mode from section 4.

**arithmetic** — `ast_arithmetic.py::validate_arithmetic_structure` (L7–45). The expression inspected is the first match of `[\d\(\)\-][\d\s\+\-\*/÷×·:\(\)\.\^a-zA-Z]+[\d\)]` — note it *includes letters*, which is why prose between digits is fatal.
- `eval_mode` must be `arithmetic` (L11–17).
- The matched expression contains no letters (L20–23).
- `addition_subtraction`: contains none of `* / ÷ × · :` (L33–38).
- `multiplication_division`: contains at least one of `* / ÷ × · :` (L39–44).
- `order_of_operations`: at least 2 operators from `+ - * / ÷ × · :`, **or** a `(`…`)` pair (L24–32).

**fractions** — `ast_arithmetic.py::validate_fractions_structure` (L48–54).
- `question_text` contains `/` or the substring `fracci` (case-insensitive). No `eval_mode` check, but section 4 still requires a derivable truth, so write the bare expression (`1/4 + 2/4`, `2/3 * 3/4`, `(3/4) / (1/2)`, `4/8 simplificado`).

**pre_algebra** — `ast_algebra.py::validate_pre_algebra_structure` (L31–67).
- `eval_mode` must be `equation` (L35–41).
- The side holding the variable must be a polynomial of **degree 1** (L42–51); `x^2 = 9` is rejected.
- With `a` = coefficient of the variable and `b` = constant on the variable's side (`is_two_step_linear`, L23–28):
  - `one_step_equations`: `a ∈ {-1, 0, 1}` **or** `b = 0` — e.g. `x + 5 = 12`, `x - 7 = 9`, `3*x = 15`, `x / 2 = 6`, `-x + 3 = 1`.
  - `two_step_equations`: `a ∉ {-1, 0, 1}` **and** `b ≠ 0` — e.g. `2*x + 4 = 12`, `4*x - 8 = 16`, `x/2 + 3 = 7` (a = 1/2 counts).

**decimals_percentages** — `ast_arithmetic.py::validate_decimals_percentages_structure` (L57–75).
- `percentages`: `eval_mode` is `percentage` **or** `%` appears in the text (L61–68). Use `N% de M`; `20 por ciento de 50` yields no truth.
- `decimal_operations`: the text contains a number with decimal places, regex `\d+[\.,]\d+` (L69–74). `¿Cuánto es 3 + 4?` is rejected under this subconcept; `¿Cuánto es 2.5 + 1.25?` → `3.75`.

---

## 6. Distractor explanation rules

`DistractorConsistencyValidator` (`backend/src/modes/quiz/validation/distractor_consistency.py`) with patterns from `distractor_patterns.py`.

- **Length:** ≥ 10 characters after trimming (`MIN_EXPLANATION_LENGTH`, `distractor_patterns.py` L5; checked L47–52).
- **Never claim the wrong option is right** (`INVALID_CLAIM_PATTERNS`, L54–63): the phrases `es la respuesta correcta`, `es la opción correcta`, `es la solución correcta`, `obtendrías [el error de | la] respuesta A–D`, `[el|al] valor de la opción A–D` are rejected. **Never mention option letters at all.**
- **Numeric claims must equal this option's value** (`RESULT_CLAIM_PATTERNS`, L7–52; checked L61–78). The validator extracts every number `N` (`-?\d+([.,]\d+)?(/\d+)?`) that follows one of these triggers, and if *any* were found, at least one must equal the option value numerically, else: *"Distractor 'X' explanation claims result 'N', which contradicts option value 'V'."*
  - `obtendrías / obtendrían / obtiene / obtienes / obteniendo / obtuvo / obtener` [`un resultado de` | `el valor de` | `x =`] `N`
  - `da / dando / dando como resultado / dio` [`un resultado de` | `x =`] `N` — **no word boundary**: `cada 5`, `queda 8`, `nada 3`, `toda 4`, `ayuda 2` all trigger (verified: `Cada 3 unidades…` on option `10/2` → claims `3`).
  - `resultado es / sería / da / de` [`x =`] `N`
  - `resultando en / resulta en` [`x =`] `N`
  - `queda / quedando [la ecuación] [como] x = N`
  - `lleva a / lleva al [un resultado de | un error de] N`
  - `equivale a / igual a N`
  - any written step `<digit or )> <+ - * / ÷ × ·> <digit or (> = N` — e.g. `12 / 2 = 6`, `4 + 4 = 8`, `(21 - 6 = 15)`.

  Therefore: **name exactly the option's own value, or name no number at all.** Intermediate steps are the classic failure — `Dividiste 12 / 2 = 6 y restaste 4` on option `2` is rejected even though it correctly describes the error. Rewrite without the `= 6`: `Dividiste 12 entre 2 y restaste 4 sin dividir el 4 entre 2.` Beware: 27 of the 66 existing seed questions fail this check (they predate it and are not run through it), so copy the *exemplars in section 8*, not arbitrary seed explanations.
- **Diagnostic, never filler.** Each explanation describes the specific wrong procedure that produces *that option's value* — the student who picked it must recognise what they did. `Esta opción es incorrecta.` is worthless (and too generic to help the teacher report).

---

## 7. Pedagogy & style

- Spanish, second person singular (**tú**) past tense as in the seeds: `Restaste…`, `Olvidaste…`, `Multiplicaste…`, `Dividiste…`, `Sumaste…`.
- One short sentence per explanation, readable aloud by TTS to a 7–12 year old; no parentheses, no symbols other than the numbers you must name.
- Integers and simple fractions/decimals: two-digit operands for arithmetic, denominators ≤ 12, at most two decimal places, integer equation solutions, percentages that give whole numbers.
- Answers are non-negative unless the distractor's misconception *is* a sign error (`sign_error`, `sign_flip_error`, `sign_inversion_error`), in which case a negative distractor is fine (ASCII `-`).
- `correct_option` **balanced evenly over A/B/C/D within each batch of 20 (5 each).** The option shuffler (`backend/src/modes/quiz/generation/shuffler.py`) runs only inside `QuizQuestionGenerator.generate()`; seed and pool questions are stored exactly as authored.
- No two questions in the pool share an expression, and none repeats an existing seed question. The checker compares the bare expression (`similarity_helpers.extract_math_core`) or, failing that, the normalized text (`normalize_question_text`: lower-case, accents and `¿?¡!:;,.` removed) — so `Calcula: 12 + 7` and `¿Cuánto es 12 + 7?` count as the same question. Existing seed questions (`backend/src/modes/quiz/seed_data/*.py`), grouped by subconcept — **do not reuse any of these expressions**:
  - **arithmetic / addition_subtraction** (8): `¿Cuánto es 54 + 38?` · `¿Cuánto es 67 + 29?` · `¿Cuánto es 36 + 48?` · `¿Cuánto es 49 + 25?` · `¿Cuánto es 45 - 28?` · `¿Cuánto es 72 - 39?` · `¿Cuánto es 83 - 47?` · `¿Cuánto es 60 - 27?`
  - **arithmetic / multiplication_division** (8): `¿Cuánto es 23 * 4?` · `¿Cuánto es 24 * 3?` · `¿Cuánto es 14 * 3?` · `¿Cuánto es 16 * 4?` · `¿Cuánto es 24 / 6?` · `¿Cuánto es 56 / 8?` · `¿Cuánto es 72 / 9?` · `¿Cuánto es 45 / 5?`
  - **arithmetic / order_of_operations** (8): `¿Cuánto es 3 + 4 * 2?` · `¿Cuánto es 10 - 2 * 3?` · `¿Cuánto es 6 + 8 / 2?` · `¿Cuánto es 20 - 4 * 3?` · `¿Cuánto es 2 + 3 * 4 + 1?` · `¿Cuánto es 15 - 3 * 2 + 4?` · `¿Cuánto es 4 * 3 + 2 * 5?` · `¿Cuánto es 18 - 6 / 2?`
  - **fractions / addition_subtraction** (8): `¿Cuánto es 1/4 + 2/4?` · `¿Cuánto es 2/7 + 3/7?` · `¿Cuánto es 1/5 + 2/5?` · `¿Cuánto es 3/10 + 4/10?` · `¿Cuánto es 3/5 - 1/5?` · `¿Cuánto es 5/8 - 2/8?` · `¿Cuánto es 4/9 - 1/9?` · `¿Cuánto es 7/12 - 2/12?`
  - **fractions / multiplication_division** (4): `¿Cuánto es 2/3 * 3/4?` · `¿Cuánto es 1/2 * 2/5?` · `¿Cuánto es (3/4) / (1/2)?` · `¿Cuánto es (2/5) / (2/3)?`
  - **fractions / simplification** (4): `¿Cuánto es 4/8 simplificado?` · `¿Cuánto es 6/9 simplificado?` · `¿Cuánto es 5/10 simplificado?` · `¿Cuánto es 8/12 simplificado?`
  - **pre_algebra / one_step_equations** (8): `¿Cuál es el valor de x en: x + 5 = 12?` · `¿Cuál es el valor de x en: x - 4 = 10?` · `¿Cuál es el valor de x en: x + 8 = 20?` · `¿Cuál es el valor de x en: x - 7 = 9?` · `¿Cuál es el valor de x en: 3*x = 15?` · `¿Cuál es el valor de x en: x / 2 = 6?` · `¿Cuál es el valor de x en: 4*x = 24?` · `¿Cuál es el valor de x en: x / 3 = 5?`
  - **pre_algebra / two_step_equations** (8): `¿Cuál es el valor de x en: 2*x + 4 = 12?` · `¿Cuál es el valor de x en: 3*x + 6 = 21?` · `¿Cuál es el valor de x en: 4*x - 8 = 16?` · `¿Cuál es el valor de x en: 5*x + 10 = 35?` · `¿Cuál es el valor de x en: 2*x + 10 = 24?` · `¿Cuál es el valor de x en: 3*x - 3 = 15?` · `¿Cuál es el valor de x en: 4*x + 4 = 28?` · `¿Cuál es el valor de x en: 2*x - 6 = 14?`
  - **decimals_percentages / decimal_operations** (5): `¿Cuánto es 3.5 + 2.15?` · `¿Cuánto es 7.8 - 3.25?` · `¿Cuánto es 1.2 * 4.0?` · `¿Cuánto es 6.4 / 2.0?` · `¿Cuánto es 4.25 + 1.5?`
  - **decimals_percentages / percentages** (5): `¿Cuál es el 20% de 50?` · `¿Cuál es el 25% de 80?` · `¿Cuál es el 10% de 200?` · `¿Cuál es el 50% de 60?` · `¿Cuál es el 75% de 40?`

---

## 8. Exemplars

All three pass `QuizQuestion.model_validate`, `SymPyMathValidator`, `TaxonomyValidator` and `DistractorConsistencyValidator` (verified by running them). Pool ids are shown in place of the seed ids.

**Arithmetic** (`seed_arith_add_01`, `backend/src/modes/quiz/seed_data/arithmetic_add.py`):

```json
{
  "id": "pool_arithmetic_addition_subtraction_001",
  "schema_version": "1.0.0",
  "topic": "arithmetic",
  "subconcept": "addition_subtraction",
  "question_text": "¿Cuánto es 54 + 38?",
  "options": {"A": "82", "B": "16", "C": "92", "D": "812"},
  "correct_option": "C",
  "distractors": {
    "A": {"misconception": "alignment_error", "explanation": "Olvidaste sumar la decena que llevabas."},
    "B": {"misconception": "added_instead_of_subtracted", "explanation": "Restaste 54 - 38 en vez de sumarlos."},
    "D": {"misconception": "borrowing_error", "explanation": "Escribiste el 12 completo al lado de la suma de decenas."}
  }
}
```

**Two-step equation** (`seed_prealg_two_03`, `seed_data/pre_algebra_two_step_a.py`):

```json
{
  "id": "pool_pre_algebra_two_step_equations_001",
  "schema_version": "1.0.0",
  "topic": "pre_algebra",
  "subconcept": "two_step_equations",
  "question_text": "¿Cuál es el valor de x en: 4*x - 8 = 16?",
  "options": {"A": "24", "B": "2", "C": "6", "D": "4"},
  "correct_option": "C",
  "distractors": {
    "A": {"misconception": "forgot_division", "explanation": "Sumaste 8 (16 + 8 = 24) pero olvidaste dividir entre 4."},
    "B": {"misconception": "sign_inversion_error", "explanation": "Restaste 8 en vez de sumar 8 para cancelar el -8."},
    "D": {"misconception": "divided_before_subtracting", "explanation": "Dividiste 16 / 4 = 4 ignorando el término -8."}
  }
}
```

Note why A and D pass section 6: the written steps `16 + 8 = 24` and `16 / 4 = 4` claim exactly the value of their own option.

**Percentages** (`seed_pct_04`, `seed_data/percentages.py`):

```json
{
  "id": "pool_decimals_percentages_percentages_001",
  "schema_version": "1.0.0",
  "topic": "decimals_percentages",
  "subconcept": "percentages",
  "question_text": "¿Cuál es el 50% de 60?",
  "options": {"A": "3000", "B": "1.2", "C": "10", "D": "30"},
  "correct_option": "D",
  "distractors": {
    "A": {"misconception": "multiplied_by_percentage_directly", "explanation": "Multiplicaste 60 * 50 = 3000 sin dividir entre 100."},
    "B": {"misconception": "confused_fraction_with_percent", "explanation": "Dividiste 60 / 50 en vez de hallar el 50%."},
    "C": {"misconception": "subtracted_percentage_as_raw_number", "explanation": "Restaste 60 - 50 = 10."}
  }
}
```

**Deliberately BAD example** — parses and has the right shape, yet fails three validators. Errors quoted verbatim from a real run:

```json
{
  "id": "pool_pre_algebra_two_step_equations_002",
  "schema_version": "1.0.0",
  "topic": "pre_algebra",
  "subconcept": "two_step_equations",
  "question_text": "¿Cuál es el valor de x en: 3*x + 6 = 21?",
  "options": {"A": "5", "B": "15", "C": "10/2", "D": "1"},
  "correct_option": "A",
  "distractors": {
    "B": {"misconception": "forgot_division", "explanation": "Restaste 6 pero olvidaste dividir entre 3."},
    "C": {"misconception": "sign_error", "explanation": "Cada 3 unidades cuentan como una."},
    "D": {"misconception": "divided_before_subtracting", "explanation": "Dividiste 21 / 3 = 7 y restaste 6 sin dividir el 6 entre 3."}
  }
}
```

```text
SymPyMathValidator
    Duplicate option values: 'A' and 'C' both equal '5'
    Distractor 'C' ('10/2') equals the correct solution '5'
TaxonomyValidator
    Misconception 'sign_error' on option 'C' is invalid for subconcept 'two_step_equations'. Allowed: ['divided_before_subtracting', 'forgot_division', 'sign_inversion_error', 'subtracted_instead_of_divided'].
DistractorConsistencyValidator
    Distractor 'C' explanation claims result '3', which contradicts option value '10/2'.
    Distractor 'D' explanation claims result '7', which contradicts option value '1'.
```

(It also repeats seed `seed_prealg_two_02`, so the pool checker's novelty test would reject it a fourth time. Option B is the only clean distractor.) Had the `distractors` object been keyed on the correct letter, `model_validate` would have stopped earlier with: `Distractors must match non-correct options ['B', 'C', 'D']; got ['A', 'B', 'C']`.

---

## 9. Batch plan

320 questions, 80 per topic. Each subconcept is delivered in batches of 20 (the last batch of a subconcept is the remainder), each batch a **bare JSON array with no prose**, concatenated into one file per subconcept at `backend/src/modes/quiz/seed_data/pool/<topic>__<subconcept>.json`. `start_index` is the first `NNN` of the batch (1, 21, 41…) and ids run consecutively.

| Topic | Subconcept | Questions | Batches (`start_index`) | File |
| :--- | :--- | :---: | :--- | :--- |
| arithmetic | addition_subtraction | 27 | 20 (1) + 7 (21) | `arithmetic__addition_subtraction.json` |
| arithmetic | multiplication_division | 27 | 20 (1) + 7 (21) | `arithmetic__multiplication_division.json` |
| arithmetic | order_of_operations | 26 | 20 (1) + 6 (21) | `arithmetic__order_of_operations.json` |
| fractions | addition_subtraction | 27 | 20 (1) + 7 (21) | `fractions__addition_subtraction.json` |
| fractions | multiplication_division | 27 | 20 (1) + 7 (21) | `fractions__multiplication_division.json` |
| fractions | simplification | 26 | 20 (1) + 6 (21) | `fractions__simplification.json` |
| pre_algebra | one_step_equations | 40 | 20 (1) + 20 (21) | `pre_algebra__one_step_equations.json` |
| pre_algebra | two_step_equations | 40 | 20 (1) + 20 (21) | `pre_algebra__two_step_equations.json` |
| decimals_percentages | decimal_operations | 40 | 20 (1) + 20 (21) | `decimals_percentages__decimal_operations.json` |
| decimals_percentages | percentages | 40 | 20 (1) + 20 (21) | `decimals_percentages__percentages.json` |

Check every file with (from `backend/`):

```bash
python -m pytest tests/modes/quiz/seed_data/test_pool.py -o addopts="--strict-markers" -q
```

The failing ids and their error lists are printed in one assertion message; fix and re-run until it is green.

---

## 10. The generation prompt

Paste the brief (sections 2–8) first, then this block with the four placeholders filled in:

````text
You are authoring diagnostic multiple-choice math questions for TutorBox, an offline classroom
quiz appliance for Spanish-speaking primary-school students. Your output is validated by
deterministic code (SymPy + regex), not by a human, so follow "the brief" (sections 2–8 above)
literally: it is derived from that code.

TASK
Write exactly {count} questions for topic "{topic}", subconcept "{subconcept}".
Ids run from pool_{topic}_{subconcept}_{start_index} upward, zero-padded to 3 digits, consecutive.

OUTPUT
A single JSON array of {count} objects and nothing else — no prose, no markdown fences, no
comments, no trailing commas. Each object has exactly the keys: id, schema_version, topic,
subconcept, question_text, options, correct_option, distractors (brief §2).

HOW TO BUILD EACH QUESTION
1. Pick the expression first and compute its exact value yourself (integers preferred; brief §7).
2. Write question_text using the seed phrasing for this subconcept (brief §4/§7) with exactly one
   expression and no other digits anywhere; obey the structural rule for "{subconcept}" (brief §5).
3. Pick 3 DIFFERENT misconception slugs from the "{topic}" → "{subconcept}" list in brief §3.
4. For each slug, actually perform that wrong procedure on your numbers to get the distractor
   value. If two of the four values coincide (numerically — 2/4 equals 1/2 equals 0.5), change the
   numbers and start over.
5. Write each explanation in Spanish, tú form, one short sentence, describing the wrong procedure
   that produces THAT option's value. Name only that option's own value, or no number at all —
   never an intermediate step like "12 / 2 = 6", never "da/obtienes/igual a N" with any other N,
   never a word ending in "da" followed by a number (brief §6).
6. Place the correct answer so that across the {count} questions correct_option is spread evenly
   over A, B, C, D (5 each per 20). Key distractors by exactly the other three letters.
7. Do not reuse any expression from the seed list in brief §7 or from earlier questions in this
   batch.

SELF-CHECK — before answering, verify every item for every question; fix, then output:
[ ] options has exactly A, B, C, D; distractors has exactly the 3 non-correct letters   → QuizQuestion.model_validate
[ ] topic/subconcept are the exact strings "{topic}" / "{subconcept}"                   → TaxonomyValidator
[ ] each misconception is in the §3 list for this subconcept; the 3 slugs differ         → TaxonomyValidator / test_pool
[ ] question_text has one expression, no other digits, no "=" unless it is an equation,
    no LaTeX, no word problem                                                            → SymPyMathValidator (parser.py)
[ ] the structural rule for "{subconcept}" in §5 holds                                  → validate_math_structure
[ ] the correct option, parsed as a number/fraction, equals the value you computed       → SymPyMathValidator
[ ] no distractor equals the correct value or another distractor, numerically            → SymPyMathValidator (duplicates)
[ ] every option is a bare number, fraction a/b, decimal with a dot, or "x = n"; ASCII "-" → parse_option_expression
[ ] every explanation ≥ 10 chars, no option letters, no "es la respuesta/opción/solución
    correcta", and any number after a claim trigger equals that option's value           → DistractorConsistencyValidator
[ ] ids are pool_{topic}_{subconcept}_NNN, consecutive from {start_index}, unique        → test_pool (ids)
[ ] no expression repeats a §7 seed or another question in this batch                    → test_pool (novelty)
[ ] correct_option counts are balanced over A/B/C/D                                     → brief §7
````
