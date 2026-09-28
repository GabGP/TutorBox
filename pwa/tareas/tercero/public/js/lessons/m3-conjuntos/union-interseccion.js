// Nivel 3 · Unión e Intersección
// CNB Tercero, competencia 3 — 3.3.2 (representación gráfica de la unión y la intersección) y
// 3.3.1 (significado de la unión y la intersección). Distractor clave de la unión: contar dos
// veces lo que está en los dos conjuntos (3 + 4 = 7 en vez de 5).
import { ChoiceLesson, pickChoices, stacked } from '../shared/choice-lesson.js';
import { drawEmoji, drawText } from '../shared/draw.js';
import { aguacate, banano, elote, mango, tomate } from '../shared/art.js';
import { drawSet } from './vacio-unitario.js';

// A: the fruit Ana likes. B: the fruit Luis likes.
const A = [mango, banano, tomate];
const B = [banano, tomate, aguacate, elote];
const both = A.filter((x) => B.includes(x));
const all = [...A, ...B.filter((x) => !A.includes(x))];
const onlyA = A.filter((x) => !B.includes(x));
const onlyB = B.filter((x) => !A.includes(x));
const sameSet = (a, b) => a.length === b.length && a.every((x) => b.includes(x));

/** Two overlapping circles; `shade` paints 'union', 'inter' or 'A'; `items` puts the fruit in. */
function venn(ctx, box, { shade = null, items = true } = {}) {
  const r = Math.min(box.w * 0.27, box.h * 0.4);
  const cy = box.y + box.h * 0.55;
  const ca = box.x + box.w / 2 - r * 0.6;
  const cb = box.x + box.w / 2 + r * 0.6;
  const circle = (x) => { ctx.beginPath(); ctx.arc(x, cy, r, 0, Math.PI * 2); };
  if (shade) {
    ctx.save();
    ctx.fillStyle = '#FFD54F';
    if (shade === 'union') { circle(ca); ctx.fill(); circle(cb); ctx.fill(); }
    if (shade === 'A') { circle(ca); ctx.fill(); }
    if (shade === 'inter') { circle(ca); ctx.clip(); circle(cb); ctx.fill(); }
    ctx.restore();
  }
  ctx.lineWidth = 3;
  ctx.strokeStyle = '#1565C0'; circle(ca); ctx.stroke();
  ctx.strokeStyle = '#C62828'; circle(cb); ctx.stroke();
  drawText(ctx, 'A', { x: ca - r * 1.1, y: cy - r * 1.3, w: r * 0.5, h: r * 0.45 }, '#1565C0');
  drawText(ctx, 'B', { x: cb + r * 0.6, y: cy - r * 1.3, w: r * 0.5, h: r * 0.45 }, '#C62828');
  if (!items) return;
  const size = r * 0.42;
  const place = (list, x) => list.forEach((a, i) => drawEmoji(ctx, a, x, cy + (i - (list.length - 1) / 2) * size * 1.1, size));
  place(onlyA, ca - r * 0.45);
  place(both, (ca + cb) / 2);
  place(onlyB, cb + r * 0.45);
}

function shaded(name, order) {
  return stacked(order.map((shade) => ({ value: shade, correct: shade === name, draw: (ctx, box) => venn(ctx, box, { shade, items: false }) })));
}

export default class UnionInterseccionLesson extends ChoiceLesson {
  get intro() { return '¡Ana y Luis dicen qué frutas les gustan!'; }
  get colors() { return ['#FFF3E0', '#E3F2FD']; }

  makeRounds() {
    const scene = (ctx, box) => venn(ctx, box);
    return [
      {
        say: 'En el círculo A están las frutas que le gustan a Ana, y en el B las de Luis. ¿Qué frutas les gustan a los dos? Esa es la intersección.',
        ask: '¿Cuál es la intersección?',
        hint: 'La intersección está en medio, donde los círculos se cruzan.',
        scene,
        choices: [both, all, onlyA].map((s) => ({ correct: sameSet(s, both), draw: (ctx, box) => drawSet(ctx, box, s) })),
      },
      {
        say: 'La unión junta todas las frutas de A y de B, sin repetir. ¿Cuántos elementos tiene la unión?',
        ask: '¿Cuántos hay en la unión?',
        hint: 'Cuenta cada fruta una sola vez, aunque esté en los dos círculos.',
        scene,
        choices: pickChoices(all.length, [A.length + B.length, both.length]),
      },
      {
        say: '¿Cuántos elementos tiene la intersección de A y B?',
        ask: '¿Cuántos hay en la intersección?',
        hint: 'Cuenta solo las frutas que están en los dos círculos a la vez.',
        scene,
        choices: pickChoices(both.length, [all.length, onlyA.length]),
      },
      {
        say: '¿Qué dibujo tiene pintada la intersección?',
        ask: '¿Cuál muestra la intersección?',
        hint: 'La intersección es solo la parte donde los dos círculos se cruzan.',
        choices: shaded('inter', ['union', 'inter', 'A']),
      },
      {
        say: '¿Y qué dibujo tiene pintada la unión?',
        ask: '¿Cuál muestra la unión?',
        hint: 'La unión pinta los dos círculos completos.',
        choices: shaded('union', ['inter', 'A', 'union']),
      },
    ];
  }
}
