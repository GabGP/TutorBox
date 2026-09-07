# Quiz Match & Real-Time Voting Sessions API Specification

Technical specification for real-time classroom quiz matches, countdown voting windows, first-press vote persistence, and the deterministic **>51% Rule** in **TutorBox**.

<div align="center">

| 🏠 [TutorBox](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 [Docs](../README.md) › [REST API](README.md) › **Quiz Sessions** • **Related:** [Quiz API](quiz.md) • [Diagnostic Distractors](../architecture/diagnostic-distractors.md) • [Week 3 Milestone](../milestones/week-3-session-engine.md)

</div>

---

## Endpoint Overview

These endpoints coordinate real-time classroom quiz matches: teacher match initialization, round-by-round progression, monotonic countdown timers, student vote ingestion with database-level first-press locking (`UNIQUE(round_id, student_id)`), and algorithmic evaluation of the >51% Rule for spoken TTS remediation.

| Method | Endpoint | Authorization | Description |
| :--- | :--- | :---: | :--- |
| `POST` | `/api/v1/session` | Teacher, Admin | Create a new quiz session match in lobby state |
| `GET` | `/api/v1/session/{session_id}` | Public | Public session status and active countdown probe |
| `POST` | `/api/v1/session/{session_id}/start` | Teacher, Admin | Open first round and start voting countdown |
| `POST` | `/api/v1/session/{session_id}/vote` | Student, Staff | Ingest student vote with first-press locking |
| `POST` | `/api/v1/session/{session_id}/close` | Teacher, Admin | Close the active voting window |
| `POST` | `/api/v1/session/{session_id}/reveal` | Teacher, Admin | Aggregate votes and evaluate >51% Rule |
| `POST` | `/api/v1/session/{session_id}/next` | Teacher, Admin | Advance to next round or complete match |
| `GET` | `/api/v1/session/{session_id}/report` | Teacher, Admin | Performance summary and accuracy statistics |

---

## Detailed Contracts

### <a id="post-session"></a>`POST /api/v1/session`

Creates a new quiz session match in `lobby` state with ordered questions from the question bank.

* **Authorization**: Teacher, Admin
* **Request Body**:
  ```json
  {
    "title": "Math Review 1",
    "topic": "arithmetic",
    "question_ids": ["q_add_001", "q_add_002", "q_add_003"],
    "duration_seconds": 30
  }
  ```
* **Responses**:
  * `201 Created`:
    ```json
    {
      "id": "s_a1b2c3d4e5f6",
      "title": "Math Review 1",
      "topic": "arithmetic",
      "status": "lobby",
      "current_round_index": 0,
      "question_count": 3,
      "current_round": null
    }
    ```
  * `401 Unauthorized`: Missing or invalid session token.
  * `403 Forbidden`: Caller is not a teacher or admin.

---

### <a id="get-session-id"></a>`GET /api/v1/session/{session_id}`

Publicly inspectable state of a session and active round countdown. Polled by student voting clients and projector displays.

* **Authorization**: Public
* **Path Parameters**:
  * `session_id` (`string`, required): Unique session identifier.
* **Responses**:
  * `200 OK`:
    ```json
    {
      "id": "s_a1b2c3d4e5f6",
      "title": "Math Review 1",
      "topic": "arithmetic",
      "status": "active",
      "current_round_index": 0,
      "question_count": 3,
      "current_round": {
        "round_id": "r_001_uuid",
        "round_index": 0,
        "status": "open",
        "question_id": "q_add_001",
        "duration_seconds": 30,
        "time_remaining": 22.5
      }
    }
    ```
  * `404 Not Found`: Session not found.

---

### <a id="post-session-start"></a>`POST /api/v1/session/{session_id}/start`

Transitions session state from `lobby` to `active` and opens the first question round with its countdown timer.

* **Authorization**: Teacher, Admin
* **Path Parameters**:
  * `session_id` (`string`, required): Unique session identifier.
* **Responses**:
  * `200 OK`: `SessionStateResponse` (status `active`, round 0 status `open`).
  * `404 Not Found`: Session or initial round not found.
  * `409 Conflict`: Session is not in `lobby` state.

---

### <a id="post-session-vote"></a>`POST /api/v1/session/{session_id}/vote`

Ingests a student vote. Enforces **first-press locking** at both engine and database layers (`UNIQUE(round_id, student_id)`).

* **Authorization**: Student, Teacher, Admin
* **Path Parameters**:
  * `session_id` (`string`, required): Unique session identifier.
* **Request Body**:
  ```json
  {
    "selected_option": "B",
    "transport_type": "web",
    "device_id": null,
    "response_time_ms": 1450.0
  }
  ```
* **Responses**:
  * `200 OK`:
    ```json
    {
      "vote_id": "v_a1b2c3d4e5f6",
      "session_id": "s_a1b2c3d4e5f6",
      "round_id": "s_a1b2c3d4e5f6_r0",
      "student_id": 4,
      "selected_option": "B",
      "recorded_at": "2026-09-06 12:00:00"
    }
    ```
  * `400 Bad Request`: Invalid option (not `"A"`, `"B"`, `"C"`, or `"D"`).
  * `404 Not Found`: Session or active round not found.
  * `409 Conflict`: First-press lock violation (student already voted in this round) or round not in `open` state.
  * `422 Unprocessable Content`: Input validation error.

---

### <a id="post-session-close"></a>`POST /api/v1/session/{session_id}/close`

Closes the active voting window immediately, locking out any further vote submissions.

* **Authorization**: Teacher, Admin
* **Path Parameters**:
  * `session_id` (`string`, required): Unique session identifier.
* **Responses**:
  * `200 OK`: `SessionStateResponse` with current round status `closed`.
  * `404 Not Found`: Session or active round not found.
  * `409 Conflict`: Round is not in `open` state.

---

### <a id="post-session-reveal"></a>`POST /api/v1/session/{session_id}/reveal`

Reveals round results, aggregates option distribution, and evaluates the deterministic **>51% Rule**.

$$\text{trigger\_audio} \iff \exists d \in \text{Distractors} : \frac{\text{votes}(d)}{\text{total\_votes}} > 0.51$$

* **Authorization**: Teacher, Admin
* **Path Parameters**:
  * `session_id` (`string`, required): Unique session identifier.
* **Responses**:
  * `200 OK`:
    ```json
    {
      "round_id": "s_a1b2c3d4e5f6_r0",
      "status": "revealed",
      "tally": {
        "counts": { "A": 5, "B": 12, "C": 2, "D": 1 },
        "total_votes": 20,
        "percentages": { "A": 25.0, "B": 60.0, "C": 10.0, "D": 5.0 },
        "correct_option": "A",
        "correct_count": 5,
        "correct_percentage": 25.0
      },
      "decision": {
        "should_speak": true,
        "reason": "dominant_distractor_exceeded_threshold",
        "dominant_distractor": "B",
        "dominant_percentage": 60.0,
        "misconception": "added_denominators",
        "explanation": "Sumaste los denominadores en vez de mantener el común denominador."
      }
    }
    ```
  * `404 Not Found`: Session or active round not found.
  * `409 Conflict`: Round is not in `closed` state.

---

### <a id="post-session-next"></a>`POST /api/v1/session/{session_id}/next`

Advances the session to the next question round, or marks the match as `completed` if the final question has concluded.

* **Authorization**: Teacher, Admin
* **Path Parameters**:
  * `session_id` (`string`, required): Unique session identifier.
* **Responses**:
  * `200 OK`: `SessionStateResponse` with incremented `current_round_index` and round status `open`, or session status `completed`.
  * `404 Not Found`: Session not found.

---

### <a id="get-session-report"></a>`GET /api/v1/session/{session_id}/report`

Retrieves summary performance statistics, participation metrics, and average classroom accuracy for a completed quiz match.

* **Authorization**: Teacher, Admin
* **Path Parameters**:
  * `session_id` (`string`, required): Unique session identifier.
* **Responses**:
  * `200 OK`:
    ```json
    {
      "session_id": "s_a1b2c3d4e5f6",
      "title": "Math Review 1",
      "topic": "arithmetic",
      "status": "completed",
      "total_rounds": 3,
      "total_votes_cast": 58,
      "average_accuracy_percentage": 70.69
    }
    ```
  * `404 Not Found`: Session not found.

---

## Related Specifications

* **[Diagnostic Distractors](../architecture/diagnostic-distractors.md)**: Conceptual misconception taxonomy.
* **[Database Schema & ER Model](../database/README.md)**: Tables `quiz_sessions`, `quiz_session_rounds`, and `quiz_session_votes`.
* **[Week 3 Milestone Summary](../milestones/week-3-session-engine.md)**: Engine architecture and test coverage metrics.
