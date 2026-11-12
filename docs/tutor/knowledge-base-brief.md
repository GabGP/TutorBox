# Tutor Knowledge Base Authoring Brief

<div align="center">

| 🏠 [Utz'tutor](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 [Docs](../README.md) › **Tutor** › **Knowledge Base Brief** • **Related:** [Socratic Pedagogy](../architecture/socratic-pedagogy.md) • [Question Pool Brief](../quiz/question-pool-brief.md) • [Tutor API](../api/tutor.md)

</div>

---

This brief is self-contained: paste sections 2–5 into a chat with a frontier model that has **no repository access**, and the texts it returns will pass `backend/tests/modes/socratic/test_knowledge_base.py` unchanged.

## 1. Purpose

The Socratic tutor's on-device model is too small to explain or diagnose reliably, so what the tutor knows is written once, offline, and shipped as data in `backend/src/modes/socratic/knowledge_base.json`. At run time `knowledge.py` looks a text up by exact key; nothing is searched and the model composes nothing.

| Section | Key | Used by |
| :--- | :--- | :--- |
| `explanations` | topic id of `cnb_matematicas.json` | `replies.explain_fallback`: the reply to a concept question when the model is busy, unreachable or fails the guard |
| `misconceptions` | slug returned by `classify_error` | `misconception_hints.misconception_hint`: the question asked in place of the ladder hint |

## 2. JSON contract

```json
{
  "explanations": {
    "fracciones": ["Una fracción es ... ¿Qué fracción de la tortilla queda?", "..."]
  },
  "misconceptions": {
    "borrowing_error": "En {p}, mira las unidades: ¿... pedir prestada una decena?"
  }
}
```

- `explanations` has **every** topic id of `cnb_matematicas.json`, each with **2 or 3 different** texts.
- `misconceptions` has every slug `classify_error` can return (`ERROR_SLUGS` in `telemetry/error_type.py`); any other key must be a slug of `CURRICULUM_TAXONOMY`.

## 3. Rules for an explanation

Each one is checked with the guard a model reply passes (`guard.check`, mode `explain`):

- Spanish for a 6–12 year old in Guatemala, **at most 320 characters**, two to four short sentences, **ending with a question** the child can answer in their own words.
- No English: none of `the, and, is, of, to, so, we, you, what, number, step, sum` and similar, and no word with `w`, `th`, `ck`, `ph`, `wh`, `sh` (except after `de`), or ending in `-ing`, `-tion`, `-ly`.
- Speak to the child (tú). Never `el niño`, `la niña`, `el alumno`, `dile`, `pídele`, `explícale`, and no `Tutor:` or `Niño:` labels.
- Plain text only: no LaTeX, Markdown, `\`, `{`, `}` or `$`. Write `×` and `÷`.
- Name the topic or include a number, so the text is recognisably mathematics.
- **Every written equality must be true.** `3 + 4 = 7` and `1/4 + 2/4 = 3/4` are evaluated exactly by the math engine.
- Prefer local examples (tortillas, canicas, quetzales, libras) and check cultural facts (Maya numerals, the Cholq'ij) against the CNB documents.

A text may contain numbers. If the child asks mid-problem, an explanation that states that problem's answer is skipped automatically (`containment.leaks`).

## 4. Rules for a misconception question

- One or two sentences containing `{p}`, which becomes the child's problem as written (`52 - 17`).
- **No digits and no result**: the only numbers the child sees are their own problem's.
- Contains a question aimed at the faulty step, not at the whole procedure.

## 5. The generation prompt

````text
You are writing the knowledge base of Utz'tutor, an offline Socratic math tutor for
Spanish-speaking primary-school children in Guatemala. Your output is validated by
deterministic code, so follow the rules above literally.

TASK
For each id in {ids}, write {kind}: either "2 explanations" of that CNB topic, or
"1 question" for that misconception.

OUTPUT
One JSON object and nothing else: {"<id>": ["...", "..."]} for explanations,
{"<id>": "..."} for misconception questions.

SELF-CHECK before answering
[ ] explanation: Spanish, <= 320 characters, ends with "?", no English words or shapes
[ ] explanation: every "a + b = c" you wrote is true
[ ] explanation: speaks to the child, no role labels, no LaTeX or Markdown
[ ] question: contains {p}, has a "?", has no digit
````

Merge the output into `knowledge_base.json` and check it (from `backend/`):

```bash
python -m pytest tests/modes/socratic/test_knowledge_base.py -o addopts="--strict-markers" -q
```
