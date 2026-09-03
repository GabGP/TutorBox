# Week 2 Milestone: Quiz Contract & Diagnostic Distractors

<div align="center">

| 🏠 [TutorBox](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 **Docs** › **Milestones** › **Week 2 Milestone** • **Related:** [Engineering Roadmap](roadmap.md) • [Diagnostic Distractors](../architecture/diagnostic-distractors.md)

</div>

---

This document summarizes the technical deliverables, architectural implementations, and quality metrics achieved during the **Week 2 Milestone** by **Student A (Pilot)** and **Student B (Copilot)**.

---

## 1. Executive Summary & Verification Metrics
* **Theme**: *"Wrong answers are the pedagogical content"*
* **Status**: **Pilot (Student A) Complete & Green · Copilot (Student B) In Progress**
* **Backend Test Suite**: **472 / 472 passing tests** (328 new tests added in Week 2, a 227.8% expansion from Week 1).
* **Statement Coverage**: **100.00% coverage** across all source files (`pyproject.toml` enforces `--cov-fail-under=80`).
* **Linter & Formatter**: **0 errors, 0 warnings** (`ruff check backend/` and `ruff format --check backend/`).
* **Modularity Compliance**: **100% of source files $\le 150$ LoC** and **100% of test files $\le 300$ LoC** (verified automatically via `tests/test_modularity_policy.py`).
* **Seed Question Bank**: **66 curated, 100% SymPy-verified diagnostic questions** across 4 primary mathematics domains (exceeding the milestone target of $\ge 50$ questions).

---

## 2. Implemented Subsystems by Lead

### A. Student A (Pilot): Quiz Contract, Generation Pipeline, Storage & APIs
1. **Diagnostic Contract & Pedagogical Taxonomy**:
   * Pydantic validation models (`models.py`, `schema.py`) enforcing the 1-correct + 3-distractor rule with non-empty misconception slugs and age-appropriate Spanish explanations.
   * Automated LaTeX math delimiter, fraction normalization, and dollar wrapper sanitization pipeline (`sanitizer.py`) stripping `$x$`, `$$...$$`, `\(...\)`, and `\[...\]` delimiters, normalizing `\frac{a}{b} \to a/b`, and stripping stray backslashes from options on model ingestion, contract validation, and response processing to guarantee clean plain text for SQLite storage, mobile UI, and offline TTS speech.
   * Standardized curriculum taxonomy (`taxonomy.py`) across 4 domains (`arithmetic`, `fractions`, `pre_algebra`, `decimals_percentages`), 10 subconcepts, and 32 validated misconception error slugs.
2. **Multi-Layer Deterministic Alignment & Generation Pipeline**:
   * Structured JSON Schema constrained decoding (`prompt.py`, `client.py`) with OpenAI-compatible `response_format` strictly enforcing option keys `{"A", "B", "C", "D"}` and enum membership on local SLMs (`llama.cpp`), cutting schema hallucination and rejection latency.
   * Cognitive derivation prompt sequencing & anti-contradiction constraints (`prompt.py`) enforcing a 3-step mental derivation chain (Truth $\to$ Distractor derivations $\to$ Option binding) prior to JSON emission.
   * Neutral structural few-shot exemplar provider (`prompt.py`, `exemplars.py`) demonstrating JSON schema structure with generic semantic placeholders, completely preventing local quantized SLMs from copying numbers or equations from few-shot examples.
   * Deterministic taxonomy & misconception whitelist guardrail (`taxonomy_validator.py`) strictly enforcing topic, subconcept, and distractor misconception membership before invoking symbolic evaluation.
   * Deterministic distractor explanation consistency validator (`distractor_consistency.py`, `distractor_patterns.py`) verifying that numbers calculated in pedagogical explanations match assigned option values, eliminating contradictory explanations.
   * Deterministic deduplication & novelty gate (`deduplication.py`) comparing candidate questions against reference questions via text normalization and algebraic equation equivalence, rejecting duplicates and forcing question novelty.
   * Hardware-agnostic shared LLM Client package (`src/llm/`) with abstract `LLMClient` protocol, `LocalSLMClient` (connecting to local `llama.cpp` OpenAI-compatible endpoint with configurable sampling temperature and structured `response_format`), and `MockLLMClient` (for CI/CD testing), ready for multi-mode reuse in Socratic Tutor (Week 5).
   * Automated 5-stage validation pipeline (`generator.py`) retrying up to an user-defined amount of times with error feedback upon receiving malformed JSON, taxonomy mismatches, mathematical errors, distractor explanation contradictions, or duplicate seed questions.
   * Anti-guessing option and misconception shuffler (`shuffler.py`) ensuring uniform random distribution of the correct answer across `{"A", "B", "C", "D"}` and random permutation of distractor misconception ordering while strictly preserving diagnostic bindings.
3. **Universal Mathematical AST Engine (`math_engine`)**:
   * Deterministic SymPy AST parser (`parser.py`) supporting arithmetic, fractions, percentages, Spanish decimal commas (`1,5`), colon division (`6 : 2`), and linear equations.
   * Universal mathematical AST & expression structure inspector (`ast_inspector.py`, `ast_algebra.py`, `ast_arithmetic.py`) providing shared equation classification ($ax+b=c$, degree 1 polynomial analysis, operator precedence) reusable across both Classroom Quiz Mode and Socratic Tutor Mode (Week 5).
   * Decoupled `MathValidatorInterface` protocol and baseline `SymPyMathValidator` (`validator.py`) verifying mathematical truth, AST structural integrity, non-equality of distractors, and collision detection.
4. **SQLite Persistence & Curated Seed Bank**:
   * Migration `008_add_quiz_questions.sql` with CHECK constraints and compound indexes on `(topic, subconcept)` and `created_at`.
   * Repository layer (`quiz.py`, `quiz_mapper.py`) supporting CRUD, pagination, topic filtering, random match sampling, and soft deletion.
   * 66 hand-crafted, SymPy-verified diagnostic questions across 4 domains (`seed_data/`) with idempotent startup seeder (`seeder.py`).
5. **Production Versioned REST Endpoints (`/api/v1/quiz`)**:
   * `/api/v1/quiz/topics`, `/api/v1/quiz/schema`, `/api/v1/quiz/validate`, `/api/v1/quiz/generate`, and `/api/v1/quiz/questions` CRUD endpoints with RBAC enforcement and audit logging.

### B. Student B (Copilot): Mathematical Benchmarks, Validation & Jury Defense

**Interface Contracts Provided by Student A for Student B Extension:**

* **`MathValidatorInterface`** (`backend/src/quiz/validation/validator.py`):
  ```python
  class MathValidatorInterface(ABC):
      @abstractmethod
      def validate_question_math(
          self, question: QuizQuestionBase
      ) -> MathValidationResult:
          """Validates mathematical correctness of question and diagnostic distractors."""
  ```
  * **Input**: `QuizQuestionBase` — contains `question_text`, `options` (dict `{A, B, C, D}`), `correct_option`, and `distractors`.
  * **Output**: `MathValidationResult(is_valid: bool, errors: list[str], details: dict)`.
  * **Baseline**: `SymPyMathValidator` already verifies computed solution truth, distractor non-equivalence, and duplicate/collision detection. Student B may subclass it or implement `MathValidatorInterface` directly.

* **Math Engine Extension Points** (`backend/src/math_engine/parser.py`):
  * `parse_option_expression(option_text: str) -> sp.Expr | None` — Parses an option value to a SymPy expression. Handles `÷`, `×`, Spanish decimal commas (`1,5`), colon division (`6:2`).
  * `are_values_equivalent(expr_a, expr_b) -> bool` — Numeric/symbolic equivalence via float comparison ($\epsilon < 10^{-6}$) with SymPy `simplify` fallback.
  * `extract_and_solve_problem(question_text: str) -> tuple[sp.Expr | None, str]` — Extracts and computes expected mathematical truth from question text. Returns `(solution, eval_mode)` where `eval_mode ∈ {percentage, equation, arithmetic, none}`.
  * Student B may extend these functions to handle nested fractions, negative number precedence, or advanced primary-school expressions.

**Work Packages** *[In Progress / Student B to complete]*:

1. **20 Handwritten Golden Benchmark Tests**:
   * 20 challenging edge-case test cases covering arithmetic precedence ambiguities, unlike denominator fractions, and multi-step equations with fractions/negative numbers.
   * Target file: `backend/tests/quiz/validation/test_golden_benchmarks.py`.
2. **Deep Symbolic Parser Extensions**:
   * Symbolic parsing enhancements in `math_engine/parser.py` and/or `quiz/validation/validator.py` for complex primary-school expressions beyond the baseline coverage.
3. **Pedagogical Distractor Quality Review**:
   * Human review of the 66-question seed bank and LLM-generated questions targeting $\ge 90\%$ pedagogical distractor validity.
4. **Tuesday Jury Defense**: *"Diagnostic Distractors: Wrong answers are the pedagogical content"*
   1. Why random distractors lack educational value.
   2. Forcing LLM generation to target concrete arithmetic and pre-algebra misconceptions.
   3. Qualitative results and error taxonomy from human review of the generated question pool.
