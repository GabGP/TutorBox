// Lesson sanity check: `node tests/check-lessons.mjs` (from pwa/tareas/segundo). No dependencies.
//
// Catches the mistakes that are easy to ship and hard to see on a phone:
//   - two map entries loading the same lesson file (the "12 copies" bug Primero once had)
//   - a lesson without its CNB content number, or with one from another module's competency
//   - a choice round with zero or several right answers, or repeated number choices
//   - a drawing function that throws (every scene and choice is drawn once on a fake canvas)

import { MODULES } from '../public/js/data/modules.js';
import { ChoiceLesson } from '../public/js/lessons/shared/choice-lesson.js';

const errors = [];
const fail = (where, msg) => errors.push(`${where}: ${msg}`);

// A canvas context that accepts every call, so drawing code runs without a browser.
const noop = () => {};
const ctx = new Proxy({}, {
  get: (_, prop) => {
    if (String(prop).startsWith('create')) return () => ({ addColorStop: noop }); // gradients, patterns
    if (prop === 'measureText') return () => ({ width: 10 });
    return noop;
  },
  set: () => true,
});
const box = { x: 0, y: 0, w: 300, h: 200 };

const seen = new Map();
let rounds = 0;

for (const mod of MODULES) {
  for (const lesson of mod.lessons) {
    const where = `${mod.id}/${lesson.id}`;
    if (!/^\d\.\d+\.\d+$/.test(lesson.cnb || '')) fail(where, `missing CNB content number (got ${lesson.cnb})`);
    // One level per Segundo competency: m2 lessons must teach 2.x.x content, and so on.
    else if (lesson.cnb[0] !== mod.id.slice(1)) fail(where, `CNB ${lesson.cnb} is not from competencia ${mod.id.slice(1)}`);

    const path = lesson.module.toString().match(/import\(['"](.+?)['"]\)/)?.[1];
    if (seen.has(path)) fail(where, `loads the same file as ${seen.get(path)} (${path})`);
    seen.set(path, where);

    const LessonClass = (await lesson.module()).default;
    if (typeof LessonClass !== 'function') { fail(where, 'no default export'); continue; }
    if (!(LessonClass.prototype instanceof ChoiceLesson)) { fail(where, 'not a ChoiceLesson'); continue; }

    const list = LessonClass.prototype.makeRounds.call(Object.create(LessonClass.prototype));
    if (list.length < 3) fail(where, `only ${list.length} rounds`);
    list.forEach((r, i) => {
      const at = `${where} round ${i + 1}`;
      rounds++;
      if (!r.say?.trim()) fail(at, 'nothing for Q\'uq\' to say');
      if (!r.ask?.trim()) fail(at, 'empty question bar');
      const right = r.choices.filter((c) => c.correct).length;
      if (right !== 1) fail(at, `${right} correct choices (need exactly 1)`);
      if (r.choices.length < 2) fail(at, 'fewer than 2 choices');
      const values = r.choices.map((c) => c.value).filter((v) => v !== undefined);
      if (new Set(values).size !== values.length) fail(at, `repeated number choices ${values}`);
      try {
        r.scene?.(ctx, box, 0);
        r.choices.forEach((c) => c.draw(ctx, box, 0));
      } catch (err) {
        fail(at, `drawing throws: ${err.message}`);
      }
    });
  }
}

// Interaction check on the shared engine, with a fake canvas and instant timers: a wrong tap
// keeps the round, a tapped-out wrong card is ignored, a right tap advances, and stars count
// first-try answers only (all but the first round right first time -> 2 stars).
globalThis.window = { devicePixelRatio: 1, addEventListener: noop, removeEventListener: noop };
const el = {
  getContext: () => ctx, style: {}, addEventListener: noop, removeEventListener: noop,
  parentElement: { getBoundingClientRect: () => ({ width: 360, height: 640 }) },
};
globalThis.document = { getElementById: () => el };
globalThis.setTimeout = (fn) => { fn(); return 0; };

const { default: Sample } = await import('../public/js/lessons/m4-aritmetica/sumar-restar.js');
let stars = null;
const lesson = new Sample('lesson-canvas', { onComplete: (s) => { stars = s; } });
lesson.setup();
const tap = (pickRight) => {
  const n = lesson._choices.length;
  const i = lesson._choices.findIndex((c) => c.correct === pickRight);
  const b = lesson._box(lesson._choices[i], i, n);
  lesson.onTap(b.x + b.w / 2, b.y + b.h / 2);
};
tap(false);
if (lesson.round !== 0) fail('interaction', 'a wrong tap ended the round');
tap(false);
if (lesson._missed !== true || lesson.round !== 0) fail('interaction', 'retry state lost after a second wrong tap');
for (let r = 0; r < lesson.rounds.length; r++) tap(true);
if (!lesson.isComplete) fail('interaction', `lesson not complete after ${lesson.rounds.length} right taps`);
if (stars !== 2) fail('interaction', `expected 2 stars when only the first round needed a retry, got ${stars}`);

const lessons = MODULES.reduce((n, m) => n + m.lessons.length, 0);
if (errors.length) {
  console.error(`✗ ${errors.length} problem(s):\n  ${errors.join('\n  ')}`);
  process.exit(1);
}
console.log(`✓ ${lessons} lessons, ${seen.size} distinct files, ${rounds} choice rounds checked`);
