# Week 2 Milestone: Quiz Contract & Diagnostic Distractors

<div align="center">

| 🏠 [TutorBox](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 **Docs** › **Milestones** › **Week 2 Milestone** • **Related:** [Engineering Roadmap](roadmap.md) • [Diagnostic Distractors](../architecture/diagnostic-misconceptions.md)

</div>

---

This document summarizes the technical deliverables, architectural implementations, and quality metrics achieved during the **Week 2 Milestone** by **Student A (Pilot)** and **Student B (Copilot)**.

---

## 1. Executive Summary & Verification Metrics
* **Theme**: *"Wrong answers are the pedagogical content"*
* **Status**: **Pilot (Student A) Complete & Green · Copilot (Student B) In Progress**
* **Backend Test Suite**: **309 / 309 passing tests** (165 new tests added in Week 2, a 114.6% expansion from Week 1).
* **Statement Coverage**: **100.00% coverage** across all 64 source files (`pyproject.toml` enforces `--cov-fail-under=80`).
* **Linter & Formatter**: **0 errors, 0 warnings** (`ruff check backend/` and `ruff format --check backend/`).
* **Modularity Compliance**: **100% of source files $\le 150$ LoC** and **100% of test files $\le 300$ LoC** (verified automatically via `tests/test_modularity_policy.py`).
* **Seed Question Bank**: **66 curated, 100% SymPy-verified diagnostic questions** across 4 primary mathematics domains (exceeding the milestone target of $\ge 50$ questions).

---

## 2. Implemented Subsystems by Lead

### A. Student A (Pilot): Quiz Contract, Generation Pipeline, Storage & APIs
1. **Diagnostic Contract & Pedagogical Taxonomy**:
   * Pydantic validation models (`models.py`, `schema.py`) enforcing the 1-correct + 3-distractor rule with non-empty misconception slugs and age-appropriate Spanish explanations.
   * Standardized curriculum taxonomy (`taxonomy.py`) across 4 domains (`arithmetic`, `fractions`, `pre_algebra`, `decimals_percentages`), 10 subconcepts, and 32 validated misconception error slugs.
2. **LLM Generation & Rejection Pipeline**:
   * Structured prompt builder with few-shot diagnostic examples and corrective error feedback generator (`prompt.py`).
   * Hardware-agnostic `LLMClient` protocol with `MockLLMClient` (for CI/CD testing) and `LocalSLMClient` (connecting to local `llama.cpp` OpenAI-compatible endpoint) (`llm_client.py`).
   * Automated 3-stage validation pipeline (`generator.py`) retrying up to 3 times with error feedback upon receiving malformed JSON or mathematically invalid items.
3. **Mathematical AST Engine & Validator Contract**:
   * Deterministic SymPy AST parser (`parser.py`) supporting arithmetic, fractions, percentages, Spanish decimal commas (`1,5`), colon division (`6 : 2`), and linear equations.
   * Decoupled `MathValidatorInterface` protocol and baseline `SymPyMathValidator` (`validator.py`) verifying mathematical truth, non-equality of distractors, and collision detection.
4. **SQLite Persistence & Curated Seed Bank**:
   * Migration `008_add_quiz_questions.sql` with CHECK constraints and compound indexes on `(topic, subconcept)` and `created_at`.
   * Repository layer (`quiz.py`, `quiz_mapper.py`) supporting CRUD, pagination, topic filtering, random match sampling, and soft deletion.
   * 66 hand-crafted, SymPy-verified diagnostic questions across 4 domains (`seed_data/`) with idempotent startup seeder (`seeder.py`).
5. **6 Production REST Endpoints (`/quiz`)**:
   * `/quiz/topics`, `/quiz/validate`, `/quiz/generate`, and `/quiz/questions` CRUD endpoints with RBAC enforcement and audit logging.

### B. Student B (Copilot): Mathematical Benchmarks, Validation & Jury Defense
1. **20 Handwritten Golden Benchmark Tests**:
   * *[In Progress / Student B to complete]*: 20 challenging test cases covering edge-case arithmetic precedence, unlike denominator fractions, and multi-step equations with fractions/negative numbers.
2. **Deep Symbolic Parser Extensions**:
   * *[In Progress / Student B to complete]*: Symbolic parsing enhancements in `parser.py` / `validator.py` for advanced primary-school expressions.
3. **Pedagogical Distractor Quality Review**:
   * *[In Progress / Student B to complete]*: Human review of seed and generated question bank targeting $\ge 90\%$ pedagogical distractor validity.
4. **Tuesday Jury Defense**:
   * *[In Progress / Student B to complete]*: Presentation defense on *"Diagnostic Distractors: Wrong answers are the pedagogical content"*.
