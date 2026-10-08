# TutorBox — Code Review Suggestions

Review of the whole repository at commit `b7998fd` (2026-10-03). No code was changed; this file is the only output.
Paths are repo-relative, with line numbers where it helps.

**Scope read:** backend (`src/`, migrations, config, tests harness), `pwa/pilas`, the React app in `pwa/app` (app shell, API layer, session engine, teacher/student flows, voting, speech, tutor), the three grade apps in `pwa/tareas` plus the Android wrapper, `infra/`, `tools/`, `docs/` and the root files.

**Verified by running (in a throwaway venv outside the repo):**

| Check | Result |
| :--- | :--- |
| `ruff check .` / `ruff format --check .` (backend, ruff 0.16.8) | clean / 364 files formatted |
| `pytest` (backend) | **1183 passed, 100.00 % statement coverage** (49 s) |
| `vitest run` (pwa/app) | **57 files, 298 tests passed** (138 s) |
| `tsc -b --noEmit` (pwa/app) | clean |

The quality gate is genuinely green. The findings below are the things a green gate does not catch. Findings marked **(proved)** were reproduced with a small script, not just inferred from reading.

---

## Priority summary

| # | Severity | Finding | Effort |
| :--- | :--- | :--- | :--- |
| C1 | Critical | Unauthenticated `POST /api/v1/quiz/validate` feeds raw text to SymPy's `eval`-based parser **(proved)** — **FIXED** | 1 line now; ~20 lines root fix |
| C2 | Critical | A 7-character tutor message (`9××9××9`) freezes the whole backend **(proved)** — **FIXED** | ~10 lines |
| H1 | High | Default teacher `teacher1` / `1234` is seeded and never forced to rotate | 1 line |
| H2 | High | Bearer tokens stored in plaintext in two tables, and they never expire — **FIXED** | ~5 lines |
| H3 | High | Username-only lockout lets any student lock the teacher out; slow brute force still works | small |
| H4 | High | `/session/{id}/next` has no state guard: a double-tap skips a question | ~10 lines |
| H5 | High | Retry feedback tells the model the *opposite* for two-step equations | ~3 lines |
| H6 | High | Client-controlled `transport_type` and `device_id` on votes; a bad value returns 500 | ~3 lines |
| M1–M14 | Medium | Ignored config, mixed timezones, TTS races, ONNX re-parse per request, unseeded question pool, … | small each |
| S1–S10 | Simplify | Two parallel clients, three copies of the grade-app engine, config declared 5×, dead code | delete-heavy |

Suggested order is at the end.

---

## 1. Critical

### C1. Unauthenticated remote code execution through `/quiz/validate` (proved)

- **Where:** `backend/src/api/quiz/validate.py:14-20` has no auth dependency, and `docs/api/quiz.md:24` documents it as *Public*.
  - It calls `SymPyMathValidator.validate_question_math` (`backend/src/modes/quiz/validation/validator.py:60-63`).
  - That calls `parse_option_expression` (`backend/src/core/math_engine/parser.py:15-27`).
  - That ends in `sp.parse_expr(option_text)`. The option text is unrestricted: the sanitizer only strips `$` and `\`.
- **Why it matters:** `sympy.parse_expr` is built on `eval()`, and SymPy's docs say never to use it on unsanitized input.
  - The project's own function evaluates Python attribute traversal: `parse_option_expression("().__class__.__mro__[1].__name__")` returns `'object'`.
  - That is the standard first step for escaping to OS-level calls.
  - Anyone on the classroom Wi-Fi can trigger it without logging in, and gets code execution as the backend user on the Jetson.
  - The same input path also gives a trivial CPU DoS (see C2).
- **Other entry points to the same sink:**
  - Teacher question create/update (`api/quiz/questions_write.py:55`, `api/quiz/questions_update.py:44`).
  - LLM output during generation.
  - `parse_equation_components` (`core/math_engine/equation_parser.py:42-64`), which allows letters and rewrites `^` to `**`.
- **Fix (smallest first):**
  1. Today, add `ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))]` to `validate_question`. Its only client, `pwa/app/src/features/question-bank/bankApi.ts:88`, already sends the bearer token, so nothing breaks.
  2. Root cause: add one `safe_parse(text)` in `core/math_engine` and route every caller through it. Keep the guard in the shared function, not in each caller.
     - Whitelist characters (digits, single-letter variables, `+ - * / ( ) . ^` and spaces; no `_`, quotes, `[` or attribute dots).
     - Cap the length.
     - Parse with `evaluate=False`, reject any `Pow` whose exponent is not a small integer, then evaluate.
     - Alternative: parse with Python's `ast` and allow only number, single-letter name, `BinOp` and `UnaryOp` nodes before building the SymPy expression.
  3. Add one adversarial test asserting the payload above is rejected.
- **How it was fixed:**
  1. **RBAC Endpoint Protection:** Added `ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))]` to `validate_question` in `backend/src/api/quiz/validate.py`. Updated `docs/api/quiz.md` and `docs/api/README.md` to classify `/api/v1/quiz/validate` as restricted to Teacher and Admin roles.
  2. **AST-Based Safe Parser (`safe_parse`):** Created `backend/src/core/math_engine/safe_parser.py` exposing `safe_parse(text: str) -> sp.Expr` and removed all calls to SymPy's `eval`-based `sp.parse_expr` across the entire codebase:
     - Enforced an input length limit (`MAX_EXPRESSION_LENGTH = 100`).
     - Enforced character whitelisting (digits, single-letter ASCII variables, whitespace, and `+ - * / ^ ( ) .`, plus normalization of Spanish operators `÷`, `×`, `·`, `:`, and decimal commas). Any disallowed symbol (including `_`, `[`, `]`, `{`, `}`, quotes, backticks, `$`) is immediately rejected.
     - Blocked attribute navigation dots with regex `(?<!\d)\.(?!\d)`.
     - Parsed inputs strictly into Python AST with `ast.parse(normalized, mode="eval")` and walked the syntax tree using `_ast_to_sympy` without calling `eval()`.
     - Allowed only `ast.Constant` (integers and floats with `abs <= 10**9`), `ast.Name` (single ASCII letter), `ast.UnaryOp` (`+`, `-`), and `ast.BinOp` (`+`, `-`, `*`, `/`, `**`).
     - Restricted powers (`ast.Pow`) to non-negative integer constant exponents in `0 <= exp <= 6`, rejecting unbounded power cascades and CPU exhaustion attacks. (A power of a power still got through this check; closed under C2.)
     - Re-routed all parsing call sites (`parse_option_expression` and `evaluate_arithmetic_expression` in `parser.py`, and `parse_equation_components` in `equation_parser.py`) through `safe_parse`.
  3. **Adversarial & RBAC Test Suite:**
     - Created `backend/tests/core/math_engine/test_safe_parser.py` and updated `backend/tests/core/math_engine/test_parser.py` with adversarial payloads (`"().__class__.__mro__[1].__name__"`, `"__import__('os').system('id')"`, `"9**9**9"`, `"9××9××9"`, attribute dots, oversized inputs) confirming safe rejection without code execution.
     - Updated `backend/tests/api/quiz/test_validate.py` with RBAC verification (unauthenticated returns 401, student returns 403, teacher/admin returns 200) and an adversarial RCE exploit attempt test.
     - Full test suite verified green with 100% statement coverage (1193 passed).

### C2. Any logged-in student can freeze every request with `9××9××9` (proved)

- **Where:**
  - `backend/src/modes/socratic/problems.py:35`: `_EXPRESSION` allows `×`.
  - `normalize` (`:66-72`) only rewrites `×` when a digit follows it, so `××` survives.
  - `_evaluate` (`:126-138`) replaces `×` with `*` and calls `sp.sympify("9**9**9")`.
  - The operand cap (`10**9`) and length cap (60) don't help: the operands are `9` and the message is 7 characters.
- **Proof:** `find_problem("9××9××9")` had not returned after 15 s. A background thread got no CPU time during that window, because the big-integer power holds the GIL.
- **Why it matters:** the backend runs a single worker (`infra/systemd/tutorbox-backend.service`), so every student, the classroom screen and the teacher stall together. Signup is open and the tutor only requires tutor mode, so any student can do this. The unauthenticated route in C1 reaches the same hang with `"9**9**9"` as an option.
- **Fix:** C1's `safe_parse` (bounded exponents) covers both. The tutor never needs exponents, though: it only handles `+ − × ÷` and parentheses, which `ast` plus `fractions.Fraction` evaluates exactly without SymPy. A cheap extra guard is to reject any operator that appears twice in a row. Add the test `assert find_problem("9××9××9") is None` with a timeout.
- **How it was fixed:**
  1. **Reproduced first, and found two more ways in.** On the code after the C1 commit, three student messages got no answer in 25 s (child process, killed at the limit):
     - `9××9××9` (7 characters), as described above.
     - The same trick through the equation path: `x+` + eleven nested `(…××6)` + `=5` (60 characters). It got past C1's `safe_parse`, whose cap bounded each exponent (≤ 6) but not their product: eleven levels is 9 to the power 6¹¹.
     - A degree-30 equation, `(x+1)××6×(x+2)××6×…×(x+5)××6=5` (46 characters), where `sp.solve` never finished.
     - Without powers, the worst equations that fit the 60-character cap answered in 0.7–1.2 s including interpreter start (nine linear factors, `x` times itself 29 times, a chain of nine reciprocals), so powers were the whole problem.
  2. **Operations no longer use an evaluator that knows powers (root cause):** new `backend/src/core/math_engine/exact_arithmetic.py` exposes `evaluate_exact(text) -> Fraction | None`.
     - It walks Python's `ast` and evaluates only numbers, unary `+`/`-` and `+ - × ÷`, with `Fraction`s. Decimals stay exact (the digits as typed, not a float) and a division by zero gives `None`. `Pow`, `//`, `%`, names and calls are not in the allow-list, so `××` (which becomes `**` in Python) is simply not arithmetic.
     - Before parsing it rejects any character outside `0-9`, whitespace and `+ - * / ( ) .` (so `1e999999999` cannot make `Fraction` build a gigantic number) and anything longer than `MAX_EXPRESSION_LENGTH` (100, shared with `safe_parse`). Leading zeros (`007 + 3`) are normalised, because SymPy used to accept them.
     - `problems._evaluate` now calls it, and `modes/socratic/problems.py` no longer imports SymPy or `eval`-based parsing at all (148 → 139 lines, under the 150 ceiling).
  3. **Equations:** `_equation` returns `None` for any equation containing `××`. The tutor has no powers, and `12 ÷ n = 3` and `2x + 4 = 12` still solve.
  4. **Closed the gap C1 left in `safe_parse`** (shared with the quiz validator and LLM output): `safe_parser.py` rejects a power whose base contains another power ("Nested powers are not supported.") before evaluating anything. Separate powers (`x**2 + 3**2`) still work.
  5. **Tests** (1193 → 1230 passing, 100 % statement coverage kept):
     - `tests/core/math_engine/test_exact_arithmetic.py` (new): 16 exact cases (decimals, fractions, unary signs, leading zeros, a 19-digit decimal) and 16 inputs that must return `None` (`9××9××9`, `9**9**9`, `//`, `%`, divide by zero, names, calls, `1e999999999`, empty, too long).
     - `test_safe_parser.py`: a power of a power is rejected at any depth, separate powers are still allowed.
     - `test_problems.py`: four hostile messages join the "no solvable problem" list (the three above and `x + 3××2 = 11`), and `find_attempt("9××9 = 5")` is `None`.
  6. **Verified:** `ruff check` and `ruff format --check` clean. The same probe on the fixed code returns `None` in under 1 s for all three messages, and decimals, fractions, `12 ÷ n = 3`, `2x + 4 = 12` and `007 + 3` still solve. `docs/api/tutor.md` now says the tutor computes exactly and lists the bound as a guardrail.
  - **Limits:** there is no timeout test. If the fix regressed, the test run would hang instead of failing, because an in-process timer cannot run while a big-integer power holds the GIL. Equations still go through `sp.solve`, so staff or LLM text containing a flat high-degree polynomial (`(x+1)**6*(x+2)**6*…`) is bounded only by the 100-character cap, not by degree; checking the polynomial degree before `sp.solve` would close it.

---

## 2. High

### H1. Seeded teacher `teacher1` / `1234`, never forced to change the PIN

- **Where:** `backend/src/core/config/constants.py:17-18`, `.env.example:38-39`, and `backend/src/core/db/seed_users.py:32-36` (it inserts without `must_change_pin`). `pwa/README.md:39` publishes the credentials.
- **Why it matters:** a student who logs in as `teacher1` can reset any student's *or teacher's* PIN and read the temporary PIN from the response (`api/staff/user_reset_pin.py:47-72`). They can also delete accounts and change roles.
- **Fix:** reuse the mechanism that already exists by inserting the seed teacher with `must_change_pin = 1`. That's one column in the INSERT; `ensure_no_pending_rotation` and `ForcedPinModal` handle the rest.

### H2. Session tokens are stored in plaintext and never expire

- **Where:**
  - `backend/src/api/auth/login.py:62-66` stores the bearer UUID as `sessions.id`.
  - `core/security/auth_session.py:41-49` looks it up.
  - `api/tutor/endpoints.py:46-47,97-112` writes the same token into `turn_logs.session_id`.
  - This contradicts the project's own rule that tokens "must never appear in … DB columns".
  - `sessions.created_at` exists but nothing checks it, so a token copied from a shared tablet works until logout or a PIN change.
- **Fix:**
  - Store `hashlib.sha256(token.encode()).hexdigest()` at login and in the lookup and deactivate queries (about 3 lines). Use the same hash in `turn_logs` so the foreign key stays valid.
  - Add `AND s.created_at > datetime('now', '-12 hours')` (or a setting) to the lookup.
- **How it was fixed:**
  1. **Hashed once, in the function every request goes through.** `core/security/auth_session.py` adds `token_digest(token)`, the SHA-256 hex of the token. A fast hash is enough because tokens are random UUIDs (122 bits). `get_current_session` looks up `sessions.id = token_digest(bearer)` and returns that digest as `AuthContext.session_id`.
     - Logout, PIN and username changes, and the tutor (`turn_logs.session_id`, plus its per-login turn gate and conversation keys) all use `ctx.session_id`. They now store and compare the digest without any change of their own, so the `turn_logs` foreign key stays valid.
     - `api/auth/login.py` stores the digest and returns the token to the client once. No table, log or in-memory key keeps the token after the request that carries it.
  2. **Expiry.** The lookup also requires `s.created_at > datetime('now', '-12 hours')`. `SESSION_TTL_HOURS = 12` covers one school day. It is a constant rather than a setting, because `core/config/models.py` is already at the 150-line ceiling and no school has asked for another length. An expired session gets the existing `401 Invalid or expired session.`
  3. **Existing rows: no migration.** Rows written before the fix keep their old UUID in `sessions.id` and `turn_logs.session_id`, but those can no longer log in: a 36-character UUID never equals a 64-character digest. Deleting them would cascade-delete their tutor turns (`ON DELETE CASCADE`). Everyone logs in once more after the upgrade.
  4. **Tests** (1544 → 1546 passing, 100% statement coverage):
     - login stores the digest, and the raw token appears nowhere in `sessions`;
     - logout deactivates the digest's row, and `AuthContext.session_id` is the digest;
     - a session 11 hours old works and one 13 hours old gets 401;
     - a token stored in plaintext (an old row) no longer authenticates;
     - tutor turns log the digest, never the token.
  5. **Verified:** `ruff check` and `ruff format --check` clean, 1546 passed, coverage 100%.
  - **Limits:** the 12 hours count from login, not from the last request, so a student who logs in at 7:00 must log in again at 19:00 even while active. The old plaintext UUIDs stay in the two tables, unusable.

### H3. The lockout is a classroom DoS, and still allows slow brute force

- **Where:** `backend/src/core/security/rate_limit/lockout.py` is keyed by username only (5 failures, then a 30 s lockout).
- **Why it matters:**
  - Five wrong PINs for `teacher1` every 30 s keeps the teacher locked out for the whole class.
  - The other way round, 10 tries a minute cracks a 4-digit PIN in about 8 h on average.
  - Smaller issue: unknown usernames return before bcrypt runs (`api/auth/login.py:37-43`), so response time reveals which usernames exist. Signup's 409 reveals usernames anyway (`api/users/signup.py:54-61`), so pick one stance: equalize with a dummy hash, or accept that usernames are public.
- **Fix:**
  - Key failures by `(username, request.client.host)`. Uvicorn already resolves the client IP from nginx's `X-Forwarded-For` for loopback.
  - Grow the lockout exponentially after repeated lockouts.
  - Add nginx `limit_req` on `/api/v1/auth/` and `/api/v1/users/signup`, which needs no code.
  - Consider 6-digit PINs for staff roles.

### H4. `/next` has no state guard, so a double-tap skips a question

- **Where:**
  - `backend/src/modes/quiz/session/session_manager.py:70-89` advances `current_round_index` without checking the session status or the current round's status.
  - Neither client disables the button while a request is in flight: Pilas at `pwa/pilas/maestro/index.html:408-418`, and React at `pwa/app/src/pages/teacher/teacherViewModel.ts:70-71`, where `isPrimaryDisabled` has no busy flag.
  - `TeacherView.tsx:116-119` calls `advancePrimary()` without awaiting it or adding `.catch`, so API errors become silent unhandled rejections.
- **Effects:**
  - Two taps advance twice. The skipped round stays `pending` forever.
  - `/next` also works on `lobby` and `completed` sessions.
  - A losing race raises `InvalidRoundStateError`, which `api/session/host.py:115-130` doesn't map, so it returns 500. A concurrent `/start` fails the same way.
- **Fix:**
  - Require `status == "active"` and the current round `revealed` in `advance_quiz_session`, raising `InvalidSessionStateError`. Map it, and `InvalidRoundStateError`, to 409.
  - In the clients, add a busy flag and surface errors in a toast.

### H5. Retry feedback contradicts the two-step requirement

- **Where:** `backend/src/modes/quiz/generation/protocols.py:122-134` appends *"NEVER write 2-step equations like 2x + 6 = 10"* for **any** error containing "Pedagogical mismatch" or "1-step equation". That includes the two-step rejection itself (`core/math_engine/ast_algebra.py:53-59`: "requires a 2-step equation … but received a 1-step equation") and every arithmetic, fraction and percentage mismatch.
- **Effect:** each retry for `two_step_equations` pushes the model further from the target.
- **Fix:** emit the one-step instruction only when the error names `one_step_equations` and add the symmetric two-step hint. Alternatively, drop it, since the error text is already explicit. Add a one-line test that the two-step feedback does not contain "NEVER write 2-step".

### H6. Vote transport is client-declared

- **Where:**
  - `backend/src/api/session/schemas.py:17-23` declares `transport_type: str` and `device_id: str | None` with no constraints.
  - A value outside `web`/`hardware`/`mock` fails the DB CHECK.
  - `core/db/vote_repository.py:47-54` only translates UNIQUE violations, so this surfaces as a 500.
  - Any student can label a phone vote as `hardware` with any device id, which pollutes the W7 and W8 analytics.
- **Fix:** have the web vote endpoint set `transport_type="web"` itself and ignore `device_id`. The W7 hardware transport should authenticate devices on its own path. If the fields must stay, use `Literal[...]` and the existing `DeviceIdField`.

---

## 3. Medium

- **M1. The signup rate-limit env vars are ignored (proved).** `core/security/rate_limit/sliding_window.py:53` passes the DEFAULT constants into the singleton, so `SIGNUP_RATE_LIMIT_MAX_EVENTS=3` still gives 30. The login limiter honors its env var. Fix: call `SlidingWindowLimiter()` with no arguments. The limiter is also global, so one script can block every student's signup; consider keying it per IP.
- **M2. UTC and local timestamps are mixed in the same tables.**
  - `created_at` uses SQLite `CURRENT_TIMESTAMP` (UTC).
  - `started_at`, `ended_at`, `opened_at` and `closed_at` use `time.strftime` (local time): `modes/quiz/session/session_manager.py:64,87` and `turn_manager.py:48,73`.
  - In Guatemala (UTC−6), `started_at` lands six hours *before* `created_at`, which will skew W8 analytics.
  - Fix: use `CURRENT_TIMESTAMP` in SQL everywhere, or `time.gmtime()`.
- **M3. Session creation trusts `question_ids`.**
  - Unknown ids raise a foreign-key `IntegrityError` and return 500.
  - Soft-deleted questions are accepted.
  - The list has no maximum length (`api/session/schemas.py:13`).
  - Fix: check the ids exist with `deleted_at IS NULL` (return 422) and cap the list at about 50.
- **M4. `ABANDONED` is defined but never set.** `modes/quiz/session/models.py:14`. A new session leaves older lobby or active sessions running, and the mode switch (`api/mode.py:42-51`) only checks the newest one. Fix: on create, run `UPDATE quiz_sessions SET status='abandoned' WHERE status IN ('lobby','active')`.
- **M5. Qwen daemon requests race each other.** `core/tts/engines/qwen/daemon.py:81-117` writes a command and reads "the next line" from a shared queue with no lock. A preview plus speech request, or a double-tap, can read each other's `DONE` and play an empty or partial WAV. Fix: one `threading.Lock` around write and read. Better still, put one lock in `TTSRouter.synthesize`, since the Jetson only runs one neural TTS at a time anyway.
- **M6. The daemon's stderr is piped but never read.**
  - `daemon.py:31-40`: llama.cpp logs to stderr. Once the 64 KB pipe buffer fills, the daemon blocks, synthesis times out, and the 1.7B model reloads.
  - `_wait_for_ready` (`:57-68`) calls `_read_stderr()`, a blocking `.read()` on a live process, *before* `close()`. If the first line isn't `READY`, startup can hang.
  - Fix: `stderr=subprocess.DEVNULL` (or a log file), and close before reading.
- **M7. Sherpa re-parses the ONNX model on every TTS request.**
  - `SherpaBackend.is_available` goes through `resolve_sherpa_paths` to `ensure_sherpa_model`, which calls `onnx.load()` (`core/tts/engines/sherpa/metadata.py:21-29`).
  - `get_auto_backends` (`core/tts/router/selection.py:31-40`) checks *every* engine with no short-circuit, on each speech, status, load and preview request.
  - The metadata injection can even `onnx.save` a new model file mid-request (`metadata.py:64`).
  - `tools/download_models.py` already generates the Sherpa model and tokens (`generate_sherpa_model`, `generate_sherpa_tokens`).
  - Fix: make `is_available` a file-existence check and delete the runtime metadata and token generation (`sherpa/metadata.py`, `sherpa/models.py:42-72`). That also removes `onnx` (and its protobuf) from the runtime dependencies, which helps the 8 GB budget.
- **M8. A hidden second LLM call drops the JSON schema.** `modes/quiz/generation/attempt_runner.py:21-31` catches `TypeError` and calls the model again without `response_format`. `LocalSLMClient._parse_completion_response` raises `TypeError` for malformed replies (`core/llm/client.py:93-108`). So one bad reply triggers a second slow generation with no constrained decoding. Fix: delete the fallback; every `LLMClient` already accepts `response_format`.
- **M9. The 320 authored pool questions are never seeded.** `modes/quiz/seed_data/pool/*.json` is validated by `tests/modes/quiz/seed_data/test_pool.py` ("can be wired into the seed bank unchanged"), but `seed_question_bank` only inserts the 66 Python-literal questions. Fix: load the pool JSON in `seeder.py` (a few lines). Then turn the 16 Python seed modules into JSON too; they were split only to fit the 150-line rule (see S3).
- **M10. Dedup ignores the live bank.** `modes/quiz/validation/deduplication.py:35-39` compares against `SEED_QUESTIONS` only, so the model can regenerate a question that's already saved. Fix: pass the bank's questions for that topic from the DB.
- **M11. Misconception labels say the opposite of what happened.**
  - In `seed_data/arithmetic_add.py` (`seed_arith_add_01`, option B, *"Restaste 54 - 38 en vez de sumarlos"*), a subtraction mistake is tagged `added_instead_of_subtracted`.
  - Carry errors in addition are tagged `borrowing_error` or `alignment_error`, because the taxonomy only has `forgot_carry` under `multiplication_division` (`contracts/taxonomy.py:5-16`).
  - W8 analytics will report the wrong misconceptions. Fix: add a direction-neutral `wrong_operation` and an addition-side `forgot_carry`, then relabel the seeds.
- **M12. The "SymPy truth" is extracted from free text.**
  - `evaluate_arithmetic_expression` (`core/math_engine/parser.py:58-71`) takes the first run of three or more digit/operator characters. For *"vende 125 lápices y luego 30 más"* the truth becomes `125`, so valid word problems get rejected.
  - A Spanish *"y"* after an equation is read as a variable.
  - Longer term: have the model emit a machine-readable `expression` field (SymPy checks it), and only check that the display text contains it.
- **M13. The React student score counts rejected votes.** `pwa/app/src/features/voting/useStudentVoting.ts:86-89` stores the vote locally on *any* 409, including "Voting window has expired". `recordHit` can then count a correct answer the server refused. Pilas deliberately doesn't do this (`pwa/pilas/alumno/index.html:237`). Fix: don't store on 409. Better: return the caller's own vote in the session state (it's already in `quiz_session_votes`), so the score isn't localStorage-only.
- **M14. Explain mode has no leak check.** `guard.check` only runs `leaks()` when `problem` is set, and explain turns pass `problem=None` (`modes/socratic/engine.py:70-78`). An operation written in number words (*"doscientos treinta y siete más …"*) skips `find_problem` and can reach explain mode, where the model may state the result. Low frequency, but the tutor contract is "never the answer".

---

## 4. Low / correctness nits

- **L1. Icons served with the wrong type.** `api/pwa_assets.py:24-28` serves SVG bytes as `image/png` (apple-touch-icon) and `image/x-icon`, and `pwa/app/index.html` points `apple-touch-icon` at an SVG. iOS needs a real PNG. The grade apps already ship PNG icons via `tools/render-icons.py`.
- **L2. No subprocess timeout for Piper.** The Piper CLI fallback has none (`core/tts/engines/piper/engine.py:116-119`), while eSpeak does.
- **L3. Model config rewritten during synthesis.** `sanitize_model_config` rewrites the model's JSON on every synthesis call (`core/tts/engines/piper/models.py:30-42`). Do it once at download.
- **L4. LLM proxy passes upstream status codes through.** `api/llm/proxy.py:40-47` forwards the upstream status, so an upstream 401 looks like an expired TutorBox session to the PWA. Map it to 502.
- **L5. Old tutor sessions are never evicted.** `TurnGate._recent` keeps one entry per session forever (`api/tutor/gate.py:29,50`). Prune empty deques.
- **L6. Flawed tar extraction check.** `tools/download_models.py:48-55` validates paths with `startswith` (prefix bug, ignores symlink members). Use stdlib `archive.extractall(path, filter="data")` (Python ≥ 3.11.4).
- **L7. Downloads are neither pinned nor verified.** Model downloads use `resolve/main` with no checksum (`tools/download_models.py:36-45`). Pin Hugging Face revisions and verify SHA-256. GGUF and ONNX files are parsed in-process.
- **L8. Grade-app service workers keep stale code.**
  - They're cache-first with a manually bumped `CACHE_VERSION` (primero `v6`, segundo and tercero `v1`), so students keep old JS until someone remembers to bump it.
  - `cache.addAll(...).catch(warn)` installs an empty cache silently (`pwa/tareas/*/public/sw.js`).
  - The header comment promises "network-first for API", but no such branch exists.
  - Fix: use stale-while-revalidate, or derive the version from file hashes in `check-lessons.mjs`.
- **L9. `.env.example` drift.**
  - `SLM_TEMPERATURE=0.5` but its comment says "Default: 0.7".
  - `TTS_MOSS_MODEL` and `TTS_MELO_VOICE`, and the engine names `melo` and `moss-nano` (`core/config/tts_settings.py:40-52`), are accepted with no backend behind them. They're benchmark-only; keep them in `tools/benchmark`.
- **L10. Backend port exposed on Wi-Fi.** The systemd unit binds uvicorn to `0.0.0.0:8000` while nginx proxies loopback, so port 8000 is open on the classroom Wi-Fi and bypasses anything nginx adds later. Bind to `127.0.0.1`.
- **L11. One LLM endpoint, two models.** The quiz model (Gemma, per README) and the tutor model (DeepSeek-R1-Distill 1.5B, Ollama-style name in `core/config/tutor_settings.py:19`) share `SLM_BASE_URL`. In llama-server single-model mode the `model` field is ignored, and switching `/mode` doesn't swap models. Decide between Ollama (model per request) and llama-server router mode, and tie model residency to the mode switch.
- **L12. Unbounded option text.** `options: dict[str, str]` has no per-option length limit (`modes/quiz/contracts/models.py:50`). The unused `QuestionOptions` class (`:31-38`) already has A–D fields; add `max_length` to them, use it, and delete the manual key check.
- **L13. Over-engineered result type.** `GenerationResult` (`modes/quiz/generation/types.py:17-31`) hand-writes `__iter__`, `__getitem__` and `__getattr__`. A one-line `typing.NamedTuple` gives all three.
- **L14. LLM-supplied ids reused.** The id in the model's JSON is reused when present (`modes/quiz/generation/response_processor.py:32-39`), so a collision means a 500 on save. Always mint ids on the server.
- **L15. eSpeak voice listing spawned repeatedly.** `espeak --voices` runs as a subprocess on every `is_available`, `is_loaded` and synthesis call (`core/tts/engines/espeak/cli.py:42-59`). Add `@functools.cache`.

---

## 5. Simplify (delete before adding)

- **S1. Two classroom clients with "strict 1-to-1 parity".**
  - Pilas is about 1.4 K lines in total. The React app is about 12.1 K lines of TS/TSX, plus 6 K lines of tests and 4.5 K lines of CSS.
  - `backend/src/main.py:30-38` makes React the default and calls Pilas "legacy", while `pwa/README.md:16-21` calls Pilas "the shipped Classroom Quiz client".
  - Every feature costs twice. Pick one.
  - If React stays, delete Pilas, point the backend tests at a tiny fixture dir, and drop the `tb.css` copy from Pilas in `pwa/app/vite.config.ts:19-23`.
- **S2. Three copies of the grade-app engine.**
  - About 3,000 lines are byte-identical in `pwa/tareas/{primero,segundo,tercero}/public` (`app.js`, `kuk.js`, `engine/{animation,canvas,scene,touch}.js`, `screens/{lesson,map,profile}.js`, `lessons/shared/art.js`, `css/styles.css`), so about 6,000 lines are redundant.
  - `progress.js`, `audio.js`, `draw.js`, `choice-lesson.js`, `parent.js`, `sw.js`, `check-lessons.mjs` and `render-icons.py` are near-identical.
  - Drift has already started: the thousands-comma TTS fix exists only in `tercero/public/js/engine/audio.js:155-157`.
  - Smallest step: a check (in `check-lessons.mjs` or CI) that the shared files stay byte-identical.
  - Then a `common/` folder. Android already merges several asset dirs (`pwa/tareas/android/app/build.gradle:46-51`), and the backend can mount `/tareas/common`.
- **S3. Every setting is declared 4–5 times.**
  - The chain is `constants.py` → re-exported in `core/config/__init__.py` (149 lines, mostly `DEFAULT_*` re-exports) → dataclass default in `models.py` → parse call in `settings.py`/`tts_settings.py` → `.env.example`.
  - Delete the re-export block and let the dataclass defaults be the single default.
  - The 150-line rule is also why seed data is split into 16 Python modules; data belongs in JSON (M9).
- **S4. Settings reloaded on every hot path.** `get_settings(reload=True)` appears at 9 production call sites, and `get_db_path` and `get_busy_timeout_ms` default to `reload=True` (`core/db/database.py:18-25`). Every DB connection re-parses about 50 env vars twice. This is a test convenience leaking into runtime: use `get_settings()` in production code and the existing `clear_settings_cache()` in tests.
- **S5. Dead or test-only code:**
  - Compat aliases in `core/db/__init__.py:26-29` and `core/security/__init__.py:19-20`.
  - Deprecated `modes/quiz/generation/exemplars.py`.
  - Unused `QuestionOptions`; `SessionSummary` (an exact duplicate of `SessionReportResponse`); `TransportError`.
  - The event-listener system (`modes/quiz/session/events.py`), which nothing registers outside tests.
  - Repository functions only tests call: `get_random_questions`, `list_rounds_for_session`, `has_student_voted`, `get_votes_for_student`, `get_round_vote_distribution`, `get_generation_log_by_id`.
  - `ALLOWED_ROLES`; the `MAX_ATTEMPTS`/`MAX_TRACKED_KEYS`/`LOCKOUT_DURATION_SECONDS` alias chain.
  - `api/staff/guards.py`: both callers already run the stricter last-admin and last-teacher guards first, so `ensure_managers_remain` can never fire.
  - Trivial constants in `core/tts/constants.py` (`SUBPROCESS_SUCCESS_EXIT_CODE = 0`, `MILLISECONDS_PER_SECOND`); the `get_max_cache_entries()` import hack; ONNX Runtime DLL setup written twice (`engines/provider.py`, `engines/sherpa/runtime.py`) and called twice.
  - The router's "LRU" cache, which is actually FIFO (`core/tts/router/router.py:134-137`).
- **S6. Layering inversion.** `core/db/*` imports `modes.quiz.*` models, so the platform layer depends on a feature. That's why `seeder.py` needs function-local imports. Move the quiz repositories under `modes/quiz/`, or move the models down.
- **S7. Two import roots.** Tests import `src.main` while production imports top-level, so module singletons exist twice. CLAUDE.md documents the workaround. Import top-level in tests and drop `"."` from `pythonpath`; `_reset_rate_limiters` then loses its double loop.
- **S8. The migration runner splits on `;`** (`core/db/migrations.py:79`). Running each file with `executescript` inside explicit `BEGIN`/`COMMIT` removes the documented restriction on triggers and semicolons.
- **S9. `VoteTransport` exists only in docs** (`docs/architecture/esp32-clicker-transport.md`, the roadmap, CLAUDE.md). The `transport_type` parameter on `cast_vote` is already enough for W7. Update the docs instead of building the abstract class.
- **S10. `MockLLMClient` ships in `src/`.** Only tests use it, and it counts toward coverage.

---

## 6. Repository hygiene

- **Crash dumps are tracked.** Five `bash.exe.stackdump` files are in git (root, `backend/`, `pwa/app/`, `pwa/tareas/android/`, `pwa/tareas/tercero/`). Git Bash on Windows writes them when it crashes; this review run produced three more, which were removed again. Add `*.stackdump` to `.gitignore` and `git rm --cached` them. The APK build already excludes them (`android/app/build.gradle:53-57`).
- **Large reference documents committed.** About 47 MB of CNB PDF/DOCX files are in `pwa/tareas/cnb/`, although pre-commit's `check-added-large-files` (500 KB default) would have blocked them, so hooks weren't installed when they were committed. Move them to Git LFS or a shared drive and link them from a README.
- **A stale APK build artifact is tracked.** `pwa/tareas/descargas/primero.apk` dates from Sep 23, before the one-APK-per-grade change. `segundo.apk` and `tercero.apk` are missing. Ignore `*.apk` and run `gradlew publishApk` at deploy time.
- **A Linux-ARM-only binary is a devDependency.** `pwa/app/package.json` pins `@rolldown/binding-linux-arm64-gnu` as a regular devDependency, which breaks or warns on x64 machines. Use `optionalDependencies` or pnpm `supportedArchitectures`.
- **Stale package description.** `pwa/app/package.json` still says React is "a later milestone".
- **Leftover local caches.** `backend/src/db/__pycache__` and `backend/src/llm/__pycache__` are untracked leftovers from an older layout; delete them locally.

---

## 7. CI, tests, tooling

- **No frontend CI.** CI only runs the backend (`.github/workflows/ci-backend.yml:3-11`). Add a pnpm job (`pnpm install --frozen-lockfile && pnpm typecheck && pnpm test`) and run `node tests/check-lessons.mjs` for each grade app.
- **Coverage didn't catch the top findings.** 100 % coverage missed C1, C2, H4 and H5, because coverage counts executed lines, not hostile inputs. Add four adversarial tests:
  - an unauthenticated `/quiz/validate` request returns 401;
  - `find_problem("9××9××9")` returns quickly;
  - a double `/next` returns 409;
  - the two-step feedback prompt has no "NEVER write 2-step".
- **Ruff runs only its default rules.** Enable at least `B` (bugbear; e.g. missing `raise … from` in `api/users/signup.py:58` and `api/users/credentials.py:95`) and `S` (bandit). Also set `target-version` to `py311`: the config says `py310`, but `requires-python` is `>=3.11`.
- **Slow frontend tests.** Vitest's `fileParallelism: false` makes the suite take 138 s, 72 % of it jsdom setup. Vitest itself suggests `pool: 'vmThreads'` or `isolate: false`.
- **Missing hooks lint.** `useSpeechPlayback.ts:262` has an `eslint-disable` directive, but the project has no ESLint. Either add `eslint-plugin-react-hooks` (exhaustive-deps catches stale closures) or remove the directive.
- **Dev tools installed on the appliance.** `run.py` runs `uv sync --all-extras` on the Jetson, which installs pytest, ruff, pre-commit, cmake and ninja. Split the extras (`dev`, `build`) and sync without dev extras in production. Move `httpx2` to dev too; only `TestClient` uses it.

---

## 8. Documentation drift

- **`README.md`:**
  - It promises WebSockets; every client polls once a second.
  - It names Gemma 4 as *the* LLM, while the tutor defaults to DeepSeek-R1-Distill via Ollama-style names (`.env.example:71-89`).
- **`pwa/README.md`:**
  - It says Pilas is the shipped client and that "nothing is served from the question bank", while `main.py` defaults to the React build, which has a bank picker (`pages/teacher/BankPickStep.tsx`).
  - Its "strict 1-to-1 parity" claim is no longer true (React adds bank management, telemetry, settings, tutor and mode switching).
- **CLAUDE.md** (local, gitignored, but it steers AI assistants):
  - Paths `config/`, `db/`, `quiz/` are now `core/config`, `core/db`, `modes/quiz`.
  - Coverage gate: it says 80, `pyproject.toml` enforces 100.
  - CI Python: it says 3.10, CI runs 3.11 and 3.12.
  - It says the tutor is "not yet built" and the session engine and TTS are "future milestones"; all three are built.
  - It references `docs/api-reference.md` and `docs/database-schema.md`, which are now `docs/api/*.md` and `docs/database/*.md`.
- **Roadmap gantt:** Week 5 is still marked *active* (it ended 2026-09-27).

---

## 9. What is already good (keep it)

- **The tutor's architecture:**
  - A deterministic planner owns the math, and the model only rewords or explains.
  - An output guard rejects leaks, new numbers, English and role-play.
  - A bounded gateway falls back to the deterministic hint when the model is slow.
- **Rejection-sampling generation** with staged validators and telemetry for every attempt.
- **Staff safety rails:** last-admin and last-teacher guards, soft delete with recovery, an append-only audit log, and forced PIN rotation after resets.
- **Network setup:** captive-portal handling, and infra runbooks that enable client isolation and remove the WAN.
- **The Android wrapper:** no INTERNET permission, an asset-only origin, and crash dumps excluded from the APK.
- **`check-lessons.mjs`:** dependency-free checks that catch real lesson mistakes.
- **A quality gate that is actually green:** 1183 backend tests at 100 %, 298 frontend tests, clean ruff and tsc.

---

## Suggested order

1. **C1 + C2:** one `safe_parse` plus auth on `/validate`. It's the same small change, and it removes both critical issues.
2. **H1, H2, H3:** small authentication diffs.
3. **H4, H5, H6, M1, M2:** correctness before the W8 analytics milestone depends on this data.
4. **M5–M7:** TTS stability and memory on the Jetson.
5. **Hygiene:** `.gitignore` additions, LFS, and a frontend CI job.
6. **S1 and S2:** they halve the cost of every future feature.
