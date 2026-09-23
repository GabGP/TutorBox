// Módulo 3 · Contar el Conjunto
// CNB Primero 4.1.2 (numeral y cantidad, de 1 a 9) y 4.1.4 (el conjunto vacío es el cero).
import { ChoiceLesson, numberChoices } from '../shared/choice-lesson.js';
import { drawBasket, drawItems } from '../shared/draw.js';

const SETS = [
  { item: '🍊', n: 4, how: '¿Cuántas naranjas', them: 'Cuéntalas' },
  { item: '🍌', n: 7, how: '¿Cuántos bananos', them: 'Cuéntalos' },
  { item: '🥑', n: 0, how: '¿Cuántos aguacates', them: 'Cuéntalos' },
  { item: '🍅', n: 9, how: '¿Cuántos tomates', them: 'Cuéntalos' },
];

function basket(ctx, box, item, n) {
  const b = { x: box.x + box.w * 0.15, y: box.y + box.h * 0.08, w: box.w * 0.7, h: box.h * 0.86 };
  drawBasket(ctx, b);
  drawItems(ctx, item, n, { x: b.x + b.w * 0.08, y: b.y, w: b.w * 0.84, h: b.h * 0.62 });
}

export default class ContarConjuntoLesson extends ChoiceLesson {
  get intro() { return '¡Vamos al mercado a contar!'; }
  get colors() { return ['#FFF3E0', '#FFE0B2']; }

  makeRounds() {
    return SETS.map(({ item, n, how, them }) => ({
      say: `${how} hay en la canasta? ${them} y toca el número.`,
      ask: `${how} hay?`,
      hint: n === 0 ? 'Mira bien la canasta. Si no hay ninguno, el número es cero.' : 'Toca cada uno con el dedo mientras cuentas.',
      scene: (ctx, box) => basket(ctx, box, item, n),
      choices: numberChoices(n, { max: 10 }),
    }));
  }
}
