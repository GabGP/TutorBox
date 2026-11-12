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
| `misconceptions` | slug returned by `classify_error` | `misconception_hints.misconception_hint`: the question asked in place of the ladder hint. Each slug has **exactly 5** questions; the problem's text picks one |
| `paraphrases` | name of a phrase the tutor repeats | `not_yet` (`knowledge.variant`): the opener of the reply to a wrong answer, **5 to 8 different** wordings, each **one sentence ending in a full stop, with no number**. Every other key is one **hint template** (`suma_0`, `resta_2_borrow`, `generic_1`, `concept_fracciones`, `worked_division`, `eq_step_producto`, `eq_worked_dos_pasos_suma`, `word_problem`, `think_first`...) read by `knowledge.phrase`, with **exactly 5 different** wordings (see section 4b) |

## 2. JSON contract

```json
{
  "explanations": {
    "fracciones": ["Una fracción es ... ¿Qué fracción de la tortilla queda?", "..."]
  },
  "misconceptions": {
    "borrowing_error": ["En {p}, mira las unidades: ¿... pedir prestada una decena?", "...", "...", "...", "..."]
  },
  "paraphrases": {
    "suma_0": ["¡Vamos a pensarlo juntos! Queremos juntar {a} y {b}. ¿Por dónde empiezas?", "...", "...", "...", "..."]
  }
}
```

- `explanations` has **every** topic id of `cnb_matematicas.json`, each with **2 or 3 different** texts.
- Hint templates use named `str.format` placeholders (`{a}`, `{b}`, `{p}` and the computed values the code passes in); literal braces are not allowed.
- `misconceptions` has every slug `classify_error` can return (`ERROR_SLUGS` in `telemetry/error_type.py`); any other key must be a slug of `CURRICULUM_TAXONOMY`. Each slug holds a list of **5 different** questions.

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

Write 5 per slug; the first is the original wording, the others ask the same thing differently. For each one:

- One or two sentences containing `{p}`, which becomes the child's problem as written (`52 - 17`).
- **No digits and no result**: the only numbers the child sees are their own problem's.
- Contains a question aimed at the faulty step, not at the whole procedure.

## 4b. Rules for the 5 wordings of a hint template

The code keeps the logic (branches, computed values) and the template picks the sentence frame. The wording is chosen with `zlib.crc32` of the problem's text, so a hint is a pure function of the problem and the level and different problems see different wordings. The first wording of a key is the original text; each other wording:

- Has **exactly the same placeholders** as the first and the **same pedagogical move** at that level (0 restates the goal, 1 names the concept, 2 isolates a smaller step, 3 is a worked example).
- Has **no digits or number words of its own** (the only numbers the child sees are the problem's and the computed ones; a table's `× 1`, `× 2` or a `100` that the first wording already has may stay). Avoid `un/una/uno` as a quantity and `cien`, `dos`... as words.
- **Never states or lets the child read off the answer.** Every wording must still pass `containment.leaks` for the problems it is used on.
- Has a question wherever the first wording has one, and **no more sentences** than it (the output guard keeps three sentences of a reply, and the wrong-answer opener is one of them). Never write `tú:` (it reads as a role label).
- Follows the language rules of section 3 and is at most 320 characters once filled in.

`tests/modes/socratic/test_hint_wordings.py` checks all of this for every wording and walks every problem of the bank with each of the five wordings forced.

## 5. The generation prompt

````text
You are writing the knowledge base of Utz'tutor, an offline Socratic math tutor for
Spanish-speaking primary-school children in Guatemala. Your output is validated by
deterministic code, so follow the rules above literally.

TASK
For each id in {ids}, write {kind}: either "2 explanations" of that CNB topic, or
"5 questions" for that misconception (the same step, asked 5 ways).

OUTPUT
One JSON object and nothing else: {"<id>": ["...", "..."]} for explanations,
{"<id>": ["...", "...", "...", "...", "..."]} for misconception questions.

SELF-CHECK before answering
[ ] explanation: Spanish, <= 320 characters, ends with "?", no English words or shapes
[ ] explanation: every "a + b = c" you wrote is true
[ ] explanation: speaks to the child, no role labels, no LaTeX or Markdown
[ ] question: all 5 contain {p}, have a "?", have no digit and differ from each other
````

Merge the output into `knowledge_base.json` and check it (from `backend/`):

```bash
python -m pytest tests/modes/socratic/test_knowledge_base.py -o addopts="--strict-markers" -q
```
