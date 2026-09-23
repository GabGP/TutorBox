// Módulo 4 · Restar Elotes
// CNB Primero 4.8.6 (restas de un dígito, sin prestar) y 4.1.4 (el cero).
import { ChoiceLesson, numberChoices } from '../shared/choice-lesson.js';
import { drawEmoji, drawItems } from '../shared/draw.js';
import { elote } from '../shared/art.js';

// Each subtraction is [total, taken]; the answer is total - taken.
const SUBS = [[5, 2], [4, 1], [7, 3], [6, 6]];

function field(ctx, box, total, taken) {
  ctx.fillStyle = '#A1887F';
  ctx.beginPath(); ctx.roundRect(box.x + box.w * 0.04, box.y + box.h * 0.1, box.w * 0.7, box.h * 0.8, 14); ctx.fill();
  drawItems(ctx, elote, total, { x: box.x + box.w * 0.06, y: box.y + box.h * 0.12, w: box.w * 0.66, h: box.h * 0.76 }, { crossed: taken });
  drawEmoji(ctx, '🐿️', box.x + box.w * 0.87, box.y + box.h * 0.6, box.w * 0.16);
}

export default class RestarElotesLesson extends ChoiceLesson {
  get intro() { return '¡Una ardilla traviesa llegó a la milpa!'; }
  get colors() { return ['#FFF8E1', '#C5E1A5']; }

  makeRounds() {
    return SUBS.map(([total, taken]) => ({
      say: `Había ${total} elotes. La ardilla se llevó ${taken === total ? 'todos' : taken}. ¿Cuántos elotes quedan?`,
      ask: `${total} − ${taken} = ?`,
      hint: taken === total ? 'Si no queda ninguno, el número es cero.' : 'Cuenta solo los elotes que no tienen la cruz roja.',
      scene: (ctx, box) => field(ctx, box, total, taken),
      choices: numberChoices(total - taken, { max: 9 }),
    }));
  }
}
