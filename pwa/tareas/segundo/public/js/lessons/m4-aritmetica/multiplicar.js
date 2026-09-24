// Nivel 4 · Multiplicar es Sumar Rápido
// CNB Segundo, competencia 4 — 4.9.2 (multiplicación de números menores o iguales a 9) y 4.9.1
// (relación de la multiplicación con la suma abreviada). Distractor típico: sumar los factores.
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { drawBasket, drawItems } from '../shared/draw.js';
import { aguacate, elote, mango, naranja, tomate } from '../shared/art.js';

function baskets(ctx, box, n, k, art) {
  const cols = n <= 3 ? n : Math.ceil(n / 2);
  const rows = Math.ceil(n / cols);
  const w = box.w / cols;
  const h = box.h / rows;
  for (let i = 0; i < n; i++) {
    const x = box.x + (i % cols) * w;
    const y = box.y + Math.floor(i / cols) * h;
    drawBasket(ctx, { x: x + w * 0.1, y: y + h * 0.35, w: w * 0.8, h: h * 0.6 });
    drawItems(ctx, art, k, { x: x + w * 0.12, y: y + h * 0.05, w: w * 0.76, h: h * 0.6 });
  }
}

function times(n, k, art, name) {
  return {
    say: `Hay ${n} canastas con ${k} ${name} en cada una. ¿Cuántos ${name} hay en total?`,
    ask: `${n} × ${k} = ?`,
    hint: `Suma ${k}, ${n} veces: ${Array(n).fill(k).join(' más ')}.`,
    scene: (ctx, box) => baskets(ctx, box, n, k, art),
    choices: pickChoices(n * k, [n + k, n * k + k]),
  };
}

export default class MultiplicarLesson extends ChoiceLesson {
  get intro() { return '¡Multiplicar es sumar el mismo número varias veces!'; }
  get colors() { return ['#FFFDE7', '#FFF3E0']; }

  makeRounds() {
    const [n, k] = [3, 5];
    return [
      times(3, 4, elote, 'elotes'),
      times(2, 5, mango, 'mangos'),
      {
        say: `Hay ${n} canastas con ${k} naranjas cada una. ¿Qué suma es igual a ${n} por ${k}?`,
        ask: `¿Qué suma es igual a ${n} × ${k}?`,
        hint: `Cada canasta tiene ${k}. Suma ${k} por cada canasta.`,
        scene: (ctx, box) => baskets(ctx, box, n, k, naranja),
        choices: pickChoices(Array(n).fill(k).join(' + '), [`${n} + ${k}`, Array(n).fill(n).join(' + ')]),
      },
      times(6, 3, tomate, 'tomates'),
      times(4, 4, aguacate, 'aguacates'),
    ];
  }
}
