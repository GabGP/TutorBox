# Quiz & Diagnostic Question Bank API Specification

Technical specification for diagnostic question generation, mathematical SymPy validation, taxonomy discovery, and question bank management in **TutorBox**.

<div align="center">

| 🏠 [TutorBox](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 [Docs](../README.md) › [REST API](README.md) › **Quiz Question Bank** • **Related:** [Sessions](sessions.md) • [Diagnostic Distractors](../architecture/diagnostic-distractors.md)

</div>

---

## Endpoint Overview

These endpoints govern the diagnostic question lifecycle: discovering curriculum taxonomy, retrieving canonical contract schemas, validating mathematical truth via SymPy, triggering on-device SLM generation with retry loops, and managing persistent question banks.

| Method | Endpoint | Authorization | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/api/v1/quiz/topics` | Public | Retrieve full curriculum taxonomy and misconception codes |
| `GET` | `/api/v1/quiz/schema` | Public | Canonical JSON Schema (Draft 2020-12) for diagnostic items |
| `POST` | `/api/v1/quiz/validate` | Public | Deterministic SymPy math validation for question items |
| `POST` | `/api/v1/quiz/generate` | Teacher, Admin | Generate new diagnostic question using local SLM with retries |
| `GET` | `/api/v1/quiz/generation-logs` | Teacher, Admin | Query historical SLM generation telemetry and rejections |
| `GET` | `/api/v1/quiz/generation-metrics` | Teacher, Admin | Aggregated SLM generation latency and reliability metrics |
| `GET` | `/api/v1/quiz/questions` | Teacher, Admin | Query and filter questions from persistent bank |
| `GET` | `/api/v1/quiz/questions/{id}` | Teacher, Admin | Fetch a single diagnostic question by unique ID |
| `POST` | `/api/v1/quiz/questions` | Teacher, Admin | Create teacher-authored question with SymPy verification |
| `DELETE` | `/api/v1/quiz/questions/{id}` | Teacher, Admin | Soft-delete a question while preserving telemetry integrity |

---

## Detailed Contracts

### <a id="get-quiz-topics"></a>`GET /api/v1/quiz/topics`

Retrieve the full primary mathematics curriculum taxonomy including topics, subconcepts, and diagnostic misconception codes.

* **Authorization**: Public
* **Responses**:
  * `200 OK`:
    ```json
    [
      {
        "name": "arithmetic",
        "subconcepts": [
          {
            "name": "addition_subtraction",
            "misconceptions": [
              "sign_error",
              "borrowing_error",
              "alignment_error",
              "added_instead_of_subtracted"
            ]
          },
          {
            "name": "order_of_operations",
            "misconceptions": [
              "left_to_right_precedence",
              "addition_before_multiplication",
              "ignored_parentheses"
            ]
          }
        ]
      },
      {
        "name": "fractions",
        "subconcepts": [
          {
            "name": "addition_subtraction",
            "misconceptions": [
              "added_denominators",
              "ignored_common_denominator",
              "subtracted_denominators"
            ]
          }
        ]
      }
    ]
    ```

---

### <a id="get-quiz-schema"></a>`GET /api/v1/quiz/schema`

Retrieve the canonical versioned JSON Schema (Draft 2020-12) for diagnostic quiz questions. Used by frontend PWAs, offline clickers, and sync engines for dynamic schema discovery and client-side payload validation.

* **Authorization**: Public
* **Responses**:
  * `200 OK`:
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
          "required": ["misconception", "explanation"],
          "title": "DistractorDetail",
          "type": "object"
        }
      },
      "properties": {
        "schema_version": {
          "default": "1.0.0",
          "description": "Contract schema version",
          "title": "Schema Version",
          "type": "string"
        },
        "topic": { "maxLength": 64, "minLength": 2, "title": "Topic", "type": "string" },
        "subconcept": { "maxLength": 64, "minLength": 2, "title": "Subconcept", "type": "string" },
        "question_text": { "maxLength": 500, "minLength": 5, "title": "Question Text", "type": "string" },
        "options": { "additionalProperties": { "type": "string" }, "title": "Options", "type": "object" },
        "correct_option": { "enum": ["A", "B", "C", "D"], "title": "Correct Option", "type": "string" },
        "distractors": { "additionalProperties": { "$ref": "#/$defs/DistractorDetail" }, "title": "Distractors", "type": "object" },
        "id": { "maxLength": 64, "minLength": 1, "title": "Id", "type": "string" }
      },
      "required": ["topic", "subconcept", "question_text", "options", "correct_option", "distractors", "id"],
      "title": "QuizQuestion",
      "type": "object",
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "$id": "https://tutorbox.local/schemas/v1/quiz_question.schema.json",
      "version": "1.0.0",
      "description": "Canonical versioned contract schema for TutorBox diagnostic multiple-choice quiz questions."
    }
    ```

---

### <a id="post-quiz-validate"></a>`POST /api/v1/quiz/validate`

Execute deterministic SymPy validation on an arbitrary multiple-choice diagnostic item without persisting it.

* **Authorization**: Public
* **Request Body**:
  ```json
  {
    "question": {
      "id": "q_val_001",
      "topic": "pre_algebra",
      "subconcept": "one_step_equations",
      "question_text": "¿Cuál es el valor de x en la ecuación x + 4 = 10?",
      "options": {
        "A": "6",
        "B": "14",
        "C": "4",
        "D": "5"
      },
      "correct_option": "A",
      "distractors": {
        "B": {
          "misconception": "sign_flip_error",
          "explanation": "Sumaste 4 a 10 en vez de restar 4."
        },
        "C": {
          "misconception": "wrong_inverse_operation",
          "explanation": "Restaste 6 en vez de restar 4."
        },
        "D": {
          "misconception": "table_lookup_error",
          "explanation": "Error menor al calcular 10 - 4."
        }
      }
    }
  }
  ```
* **Responses**:
  * `200 OK` (Valid Math):
    ```json
    {
      "is_valid": true,
      "errors": [],
      "details": {
        "eval_mode": "equation",
        "target_solution": "6"
      }
    }
    ```
  * `200 OK` (Invalid Math):
    ```json
    {
      "is_valid": false,
      "errors": [
        "Correct option 'A' ('99') does not equal computed truth '6'"
      ],
      "details": {
        "eval_mode": "equation",
        "target_solution": "6"
      }
    }
    ```
  * `422 Unprocessable Entity`: JSON schema violation (missing distractor, invalid option key).

---

### <a id="post-quiz-generate"></a>`POST /api/v1/quiz/generate`

Generate a new diagnostic question on-demand using the local SLM with the rejection and retry pipeline.

* **Authorization**: Teacher, Admin
* **Request Body**:
  ```json
  {
    "topic": "arithmetic",
    "subconcept": "addition_subtraction",
    "save_to_bank": true
  }
  ```
* **Responses**:
  * `200 OK`:
    ```json
    {
      "question": {
        "id": "q_gen_a1b2c3d4",
        "topic": "arithmetic",
        "subconcept": "addition_subtraction",
        "question_text": "¿Cuánto es 54 + 38?",
        "options": {
          "A": "82",
          "B": "16",
          "C": "92",
          "D": "812"
        },
        "correct_option": "C",
        "distractors": {
          "A": {
            "misconception": "alignment_error",
            "explanation": "Olvidaste sumar la decena que llevabas."
          },
          "B": {
            "misconception": "added_instead_of_subtracted",
            "explanation": "Restaste 54 - 38 en vez de sumarlos."
          },
          "D": {
            "misconception": "borrowing_error",
            "explanation": "Escribiste el 12 completo al lado de la suma de decenas."
          }
        },
        "source": "llm",
        "sympy_verified": true,
        "created_at": "2026-08-31 12:00:00"
      },
      "metadata": {
        "model_name": "qwen2.5-coder-1.5b",
        "attempts": 1,
        "duration_ms": 342.15,
        "rejection_history": []
      }
    }
    ```
  * `403 Forbidden`: Caller is a student or has pending PIN rotation.
  * `422 Unprocessable Entity`: Invalid topic or subconcept slug.
  * `502 Bad Gateway`: SLM generation failed all retry attempts (persists failure log to telemetry database).

---

### <a id="get-quiz-generation-logs"></a>`GET /api/v1/quiz/generation-logs`

Query historical telemetry trails of SLM quiz generation attempts, latency profiling, and rejection histories.

* **Authorization**: Teacher, Admin
* **Query Parameters**:
  * `topic` (`string`, optional): Filter by curriculum topic slug.
  * `user_id` (`integer`, optional): Filter by teacher/admin user ID.
  * `success` (`bool`, optional): Filter by generation outcome (`true` for success, `false` for failure).
  * `limit` (`integer`, optional, default: `50`, min: `1`, max: `100`): Pagination limit.
  * `offset` (`integer`, optional, default: `0`, min: `0`): Pagination offset.
* **Responses**:
  * `200 OK`:
    ```json
    {
      "logs": [
        {
          "id": 1,
          "question_id": "q_gen_a1b2c3d4",
          "user_id": 2,
          "topic": "arithmetic",
          "subconcept": "addition_subtraction",
          "model_name": "qwen2.5-coder-1.5b",
          "attempts": 1,
          "duration_ms": 342.15,
          "success": true,
          "rejection_history": [],
          "created_at": "2026-08-31 12:00:00"
        }
      ],
      "total": 1
    }
    ```
  * `403 Forbidden`: Caller is a student or has pending PIN rotation.

---

### <a id="get-quiz-generation-metrics"></a>`GET /api/v1/quiz/generation-metrics`

Calculate aggregated generation reliability, latency, and retry metrics for observability dashboards.

* **Authorization**: Teacher, Admin
* **Query Parameters**:
  * `topic` (`string`, optional): Filter metrics by curriculum topic slug.
  * `model_name` (`string`, optional): Filter metrics by SLM model identifier.
* **Responses**:
  * `200 OK`:
    ```json
    {
      "total_generations": 24,
      "successful_generations": 22,
      "failed_generations": 2,
      "success_rate": 0.9167,
      "avg_attempts": 1.25,
      "avg_duration_ms": 412.50
    }
    ```
  * `403 Forbidden`: Caller is a student or has pending PIN rotation.

---

### <a id="get-quiz-questions"></a>`GET /api/v1/quiz/questions`

Query and filter diagnostic questions from the question bank.

* **Authorization**: Teacher, Admin
* **Query Parameters**:
  * `topic` (`string`, optional): Filter by curriculum topic slug.
  * `subconcept` (`string`, optional): Filter by subconcept slug.
  * `limit` (`integer`, optional, default: `50`, min: `1`, max: `200`): Pagination limit.
  * `offset` (`integer`, optional, default: `0`, min: `0`): Pagination offset.
  * `include_deleted` (`bool`, optional, default: `false`): Include soft-deleted questions.
* **Responses**:
  * `200 OK`:
    ```json
    {
      "questions": [
        {
          "id": "seed_arith_add_01",
          "topic": "arithmetic",
          "subconcept": "addition_subtraction",
          "question_text": "¿Cuánto es 54 + 38?",
          "options": {
            "A": "82",
            "B": "16",
            "C": "92",
            "D": "812"
          },
          "correct_option": "C",
          "distractors": {
            "A": {
              "misconception": "alignment_error",
              "explanation": "Olvidaste sumar la decena que llevabas."
            },
            "B": {
              "misconception": "added_instead_of_subtracted",
              "explanation": "Restaste 54 - 38 en vez de sumarlos."
            },
            "D": {
              "misconception": "borrowing_error",
              "explanation": "Escribiste el 12 completo al lado de la suma de decenas."
            }
          },
          "source": "seed",
          "sympy_verified": true,
          "created_at": "2026-08-31 10:00:00"
        }
      ],
      "total": 66
    }
    ```
  * `403 Forbidden`: Caller is a student or has pending PIN rotation.

---

### <a id="get-quiz-questions-id"></a>`GET /api/v1/quiz/questions/{id}`

Fetch a single diagnostic question by its unique identifier.

* **Authorization**: Teacher, Admin
* **Path Parameters**:
  * `id` (`string`, required): Unique question identifier.
* **Responses**:
  * `200 OK`: Question JSON model.
  * `404 Not Found`: Question ID does not exist or is soft-deleted.

---

### <a id="post-quiz-questions"></a>`POST /api/v1/quiz/questions`

Manually create a teacher-authored diagnostic question with deterministic SymPy verification.

* **Authorization**: Teacher, Admin
* **Request Body**:
  ```json
  {
    "id": "q_teacher_manual_01",
    "topic": "fractions",
    "subconcept": "addition_subtraction",
    "question_text": "¿Cuánto es 1/4 + 2/4?",
    "options": {
      "A": "3/4",
      "B": "3/8",
      "C": "2/8",
      "D": "1/2"
    },
    "correct_option": "A",
    "distractors": {
      "B": {
        "misconception": "added_denominators",
        "explanation": "Sumaste los denominadores 4+4=8 en vez de mantener el común denominador."
      },
      "C": {
        "misconception": "multiplied_only_numerators",
        "explanation": "Multiplicaste los numeradores y sumaste denominadores."
      },
      "D": {
        "misconception": "subtracted_denominators",
        "explanation": "Confundiste 3/4 con 1/2."
      }
    }
  }
  ```
* **Responses**:
  * `201 Created`: Created `QuizQuestionResponse`.
  * `403 Forbidden`: Caller is a student or has pending PIN rotation.
  * `409 Conflict`: Question with specified `id` already exists in the bank.
  * `422 Unprocessable Content`: Mathematical validation failure or schema/taxonomy error.

---

### <a id="delete-quiz-questions-id"></a>`DELETE /api/v1/quiz/questions/{id}`

Soft-delete a diagnostic question from the question bank while retaining telemetry integrity.

* **Authorization**: Teacher, Admin
* **Path Parameters**:
  * `id` (`string`, required): Question identifier.
* **Responses**:
  * `200 OK`:
    ```json
    {
      "detail": "Question deleted."
    }
    ```
  * `403 Forbidden`: Caller is a student or has pending PIN rotation.
  * `404 Not Found`: Question not found or already deleted.

---

## Related Specifications

* **[Diagnostic Distractors Taxonomy](../architecture/diagnostic-distractors.md)**: Misconception categories and pedagogical rationale.
* **[Quiz Match & Voting Sessions](sessions.md)**: Real-time session engine executing rounds from question banks.
* **[Database Schema & ER Model](../database/README.md)**: `quiz_questions` and `quiz_generation_logs` tables.
