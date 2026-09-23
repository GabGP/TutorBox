// Módulo 4 · Sumar Jocotes
// CNB Primero 4.8.1 (sumas de dos sumandos de un dígito) y 4.8.2 (el cero como sumando).
import { ChoiceLesson, numberChoices } from '../shared/choice-lesson.js';
import { drawBasket, drawItems } from '../shared/draw.js';

// Each sum is [a, b]; the answer is a + b.
const SUMS = [[2, 1], [3, 3], [4, 0], [5, 4]];

export function drawJocote(ctx, cx, cy, size) {
  const r = size * 0.36;
  ctx.fillStyle = '#E64A19';
  ctx.beginPath(); ctx.ellipse(cx, cy, r, r * 0.88, 0, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,0.35)';
  ctx.beginPath(); ctx.arc(cx - r * 0.35, cy - r * 0.3, r * 0.25, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#558B2F';
  ctx.beginPath(); ctx.ellipse(cx + r * 0.3, cy - r * 1.05, r * 0.35, r * 0.15, -0.5, 0, Math.PI * 2); ctx.fill();
}

const some = (n) => (n === 0 ? 'ningún jocote' : n === 1 ? 'un jocote' : `${n} jocotes`);

function twoBaskets(ctx, box, a, b) {
  const half = box.w * 0.42;
  const slots = Math.max(a, b);
  [[box.x, a], [box.x + box.w - half, b]].forEach(([x, n]) => {
    drawBasket(ctx, { x, y: box.y + box.h * 0.4, w: half, h: box.h * 0.55 });
    drawItems(ctx, drawJocote, n, { x: x + half * 0.08, y: box.y + box.h * 0.12, w: half * 0.84, h: box.h * 0.45 }, { slots });
  });
  ctx.fillStyle = '#1F2A1F';
  ctx.font = `900 ${Math.round(box.w * 0.14)}px Nunito, sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('+', box.x + box.w / 2, box.y + box.h * 0.55);
}

export default class SumarJocotesLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a juntar jocotes!'; }
  get colors() { return ['#FFF9C4', '#DCEDC8']; }

  makeRounds() {
    return SUMS.map(([a, b]) => ({
      say: `Aquí hay ${some(a)} y allá hay ${some(b)}. ¿Cuántos jocotes hay en total?`,
      ask: `${a} + ${b} = ?`,
      hint: b === 0 ? 'Si no agregas nada, te quedan los mismos.' : 'Junta los jocotes y cuéntalos todos, uno por uno.',
      scene: (ctx, box) => twoBaskets(ctx, box, a, b),
      choices: numberChoices(a + b, { max: 18 }),
    }));
  }
}
