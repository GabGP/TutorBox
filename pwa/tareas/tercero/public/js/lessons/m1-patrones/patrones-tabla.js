// Nivel 1 · Patrones que Crecen
// CNB Tercero, competencia 1 — 1.2.1 (secuencia numérica en patrones de la naturaleza y la cultura),
// 1.5.2 (tablas para describir patrones) y 1.3.2 (patrones en figuras de su cultura: los rombos
// del güipil). Distractor principal: seguir sumando de uno en uno cuando la tabla salta.
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { drawEmoji, drawText } from '../shared/draw.js';
import { gallina, vaca } from '../shared/art.js';

function flower(ctx, cx, cy, size) {
  const r = size * 0.5;
  ctx.fillStyle = '#EC407A';
  for (let i = 0; i < 5; i++) {
    const a = (Math.PI * 2 * i) / 5 - Math.PI / 2;
    ctx.beginPath(); ctx.arc(cx + Math.cos(a) * r * 0.55, cy + Math.sin(a) * r * 0.55, r * 0.4, 0, Math.PI * 2); ctx.fill();
  }
  ctx.fillStyle = '#FDD835';
  ctx.beginPath(); ctx.arc(cx, cy, r * 0.3, 0, Math.PI * 2); ctx.fill();
}

function petal(ctx, cx, cy, size) {
  ctx.fillStyle = '#EC407A';
  ctx.beginPath(); ctx.ellipse(cx, cy, size * 0.18, size * 0.34, 0.4, 0, Math.PI * 2); ctx.fill();
}

/** Two rows: a picture in the first column, then the values; `null` is the one to find. */
function table(ctx, box, rows) {
  const cols = rows[0].values.length + 1;
  const cw = box.w / cols;
  const rh = Math.min(box.h / rows.length, cw * 1.2);
  const y0 = box.y + (box.h - rh * rows.length) / 2;
  rows.forEach((row, r) => {
    const y = y0 + r * rh;
    ctx.fillStyle = r ? '#FFFFFF' : '#FFF8E1';
    ctx.fillRect(box.x, y, box.w, rh);
    drawEmoji(ctx, row.art, box.x + cw / 2, y + rh / 2, Math.min(cw, rh) * 0.75);
    row.values.forEach((v, c) => {
      drawText(ctx, v === null ? '?' : v, { x: box.x + cw * (c + 1), y, w: cw, h: rh }, v === null ? '#EF6C00' : '#1F2A1F');
    });
  });
  ctx.strokeStyle = '#8D6E63';
  ctx.lineWidth = 2;
  for (let c = 0; c <= cols; c++) { ctx.beginPath(); ctx.moveTo(box.x + c * cw, y0); ctx.lineTo(box.x + c * cw, y0 + rh * rows.length); ctx.stroke(); }
  for (let r = 0; r <= rows.length; r++) { ctx.beginPath(); ctx.moveTo(box.x, y0 + r * rh); ctx.lineTo(box.x + box.w, y0 + r * rh); ctx.stroke(); }
}

// `tops` counts the things; each one brings `per` of the bottom row. The last bottom is asked.
function growth({ say, ask, hint, top, bottom, tops, per }) {
  const known = tops[tops.length - 2] * per;
  const answer = tops[tops.length - 1] * per;
  const bottoms = [...tops.slice(0, -1).map((n) => n * per), null];
  return {
    say,
    ask,
    hint,
    scene: (ctx, box) => table(ctx, box, [{ art: top, values: tops }, { art: bottom, values: bottoms }]),
    choices: pickChoices(answer, [known + per, answer + per, known + 1].filter((v) => v !== answer).slice(0, 2)),
  };
}

function rombo(ctx, cx, cy, r, color) {
  ctx.fillStyle = color;
  ctx.beginPath(); ctx.moveTo(cx, cy - r); ctx.lineTo(cx + r * 0.7, cy); ctx.lineTo(cx, cy + r); ctx.lineTo(cx - r * 0.7, cy); ctx.closePath(); ctx.fill();
}

const rombos = (franja) => 2 * franja - 1;

// One woven stripe per step, each with more rhombi; the last stripe is the question.
function guipil(ctx, box, steps) {
  const rh = box.h / (steps + 1);
  const colors = ['#E53935', '#FDD835', '#1E88E5', '#43A047'];
  for (let s = 1; s <= steps + 1; s++) {
    const y = box.y + rh * (s - 0.5);
    ctx.fillStyle = s % 2 ? '#6A1B9A' : '#8E24AA';
    ctx.fillRect(box.x + box.w * 0.12, y - rh * 0.45, box.w * 0.88, rh * 0.9);
    drawText(ctx, s, { x: box.x, y: y - rh / 2, w: box.w * 0.12, h: rh });
    if (s > steps) {
      drawText(ctx, '?', { x: box.x + box.w * 0.12, y: y - rh / 2, w: box.w * 0.88, h: rh }, '#FFFFFF');
      continue;
    }
    const n = rombos(s);
    const r = Math.min(rh * 0.38, (box.w * 0.8) / (n * 1.6));
    for (let i = 0; i < n; i++) {
      rombo(ctx, box.x + box.w * 0.56 + (i - (n - 1) / 2) * r * 1.5, y, r, colors[i % colors.length]);
    }
  }
}

export default class PatronesTablaLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a descubrir patrones que crecen!'; }
  get colors() { return ['#F3E5F5', '#E8F5E9']; }

  makeRounds() {
    const [petals, henLegs, cowLegs] = [5, 2, 4];
    const steps = 3;
    const answer = rombos(steps + 1);
    return [
      growth({
        say: 'La tabla cuenta los pétalos de las flores del jardín. ¿Cuántos pétalos tienen 4 flores?',
        ask: '¿Cuántos pétalos tienen 4 flores?',
        hint: `Cada flor tiene ${petals} pétalos. Abajo se cuenta de ${petals} en ${petals}.`,
        top: flower, bottom: petal, tops: [1, 2, 3, 4], per: petals,
      }),
      growth({
        say: 'Esta tabla cuenta las patas de las gallinas. ¡Cuidado, la tabla salta! ¿Cuántas patas tienen 6 gallinas?',
        ask: '¿Cuántas patas tienen 6 gallinas?',
        hint: `Cada gallina tiene ${henLegs} patas. No sigas contando de uno en uno: son 6 gallinas.`,
        top: gallina, bottom: '👣', tops: [1, 2, 3, 6], per: henLegs,
      }),
      {
        say: 'Mira cómo crecen los rombos en las franjas del güipil. ¿Cuántos rombos tendrá la franja 4?',
        ask: '¿Cuántos rombos tendrá la franja 4?',
        hint: `Cada franja tiene ${rombos(2) - rombos(1)} rombos más que la anterior.`,
        scene: (ctx, box) => guipil(ctx, box, steps),
        choices: pickChoices(answer, [rombos(steps) + 1, 2 * (steps + 1)]),
      },
      growth({
        say: 'Ahora las patas de las vacas. ¿Cuántas patas tienen 5 vacas?',
        ask: '¿Cuántas patas tienen 5 vacas?',
        hint: `Cada vaca tiene ${cowLegs} patas. Cuenta de ${cowLegs} en ${cowLegs} hasta llegar a 5 vacas.`,
        top: vaca, bottom: '👣', tops: [1, 2, 3, 5], per: cowLegs,
      }),
    ];
  }
}
