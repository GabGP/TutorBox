// Nivel 5 · Seguro, Posible o Imposible
// CNB Tercero, competencia 5 — 5.3.1 (diferenciar eventos por su probabilidad o certeza), 5.2.3
// (probabilidad para tomar decisiones), 5.2.2 (eliminación de posibilidades) y 5.3.2 (predicción
// con la información del contexto). Las respuestas salen de contar las canicas de cada bolsa.
import { ChoiceLesson, pickChoices, stacked } from '../shared/choice-lesson.js';
import { center, drawEmoji, drawNumeral } from '../shared/draw.js';

const CHANCES = ['seguro', 'posible', 'imposible'];
const chance = (k, total) => (k === 0 ? 'imposible' : k === total ? 'seguro' : 'posible');
const COLOR = { roja: '#E53935', azul: '#1E88E5', verde: '#43A047' };
const PLURAL = { roja: 'rojas', azul: 'azules', verde: 'verdes' };
const total = (bag) => Object.values(bag).reduce((a, b) => a + b, 0);

/** A cloth bag with its marbles showing. */
function drawBag(ctx, box, bag) {
  const { cx, cy } = center(box);
  const s = Math.min(box.w, box.h * 1.1) * 0.46;
  ctx.fillStyle = '#D7B98E';
  ctx.strokeStyle = '#8D6E63';
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(cx - s * 0.5, cy - s * 0.75);
  ctx.quadraticCurveTo(cx - s * 1.1, cy + s * 0.9, cx, cy + s * 0.9);
  ctx.quadraticCurveTo(cx + s * 1.1, cy + s * 0.9, cx + s * 0.5, cy - s * 0.75);
  ctx.closePath(); ctx.fill(); ctx.stroke();
  const marbles = Object.entries(bag).flatMap(([color, n]) => Array(n).fill(COLOR[color]));
  const r = s * 0.14;
  marbles.forEach((c, i) => {
    ctx.fillStyle = c;
    ctx.beginPath(); ctx.arc(cx + ((i % 3) - 1) * r * 2.4, cy - s * 0.1 + Math.floor(i / 3) * r * 2.4, r, 0, Math.PI * 2); ctx.fill();
  });
}

function draw(bag, color) {
  const n = bag[color] || 0;
  return {
    say: `Sacas una canica de la bolsa sin ver. Sacar una canica ${color}, ¿es seguro, posible o imposible?`,
    ask: `Sacar una ${color}: ¿cómo es?`,
    hint: `Cuenta las canicas ${PLURAL[color]} de la bolsa. Si son todas, es seguro. Si no hay ninguna, es imposible.`,
    scene: (ctx, box) => drawBag(ctx, box, bag),
    choices: pickChoices(chance(n, total(bag)), CHANCES),
  };
}

export default class SeguroPosibleLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a jugar con canicas y a pensar qué puede pasar!'; }
  get colors() { return ['#EFEBE9', '#E3F2FD']; }

  makeRounds() {
    // Stacked cards are not shuffled: the best bag sits in the middle.
    const bags = [{ roja: 1, azul: 4 }, { roja: 4, azul: 1 }, { roja: 2, azul: 3 }];
    const best = Math.max(...bags.map((b) => b.roja / total(b)));
    const clues = [
      [(n) => n % 2 === 0, 'no es par'],
      [(n) => n > 6, 'no es mayor que 6'],
      [(n) => n !== 10, 'no puede ser: dijimos que no es el 10'],
    ];
    const secret = Array.from({ length: 10 }, (_, i) => i + 1).filter((n) => clues.every(([ok]) => ok(n)));
    return [
      draw({ roja: 5 }, 'roja'),
      draw({ roja: 3, azul: 2 }, 'azul'),
      draw({ roja: 4, azul: 1 }, 'verde'),
      {
        say: 'Quieres sacar una canica roja. ¿De qué bolsa es más fácil sacarla?',
        ask: '¿Qué bolsa conviene para sacar roja?',
        hint: 'Todas tienen 5 canicas. Escoge la que tiene más rojas.',
        choices: stacked(bags.map((b) => ({ correct: b.roja / total(b) === best, draw: (ctx, box) => drawBag(ctx, box, b) }))),
      },
      {
        say: 'Adivina mi número: está entre 1 y 10, es par, es mayor que 6 y no es 10. ¿Cuál es?',
        ask: 'Par, mayor que 6, no es 10',
        choices: [secret[0], 6, 10].map((n) => ({
          value: n,
          correct: clues.every(([ok]) => ok(n)),
          hint: `El ${n} ${clues.find(([ok]) => !ok(n))?.[1] ?? ''}. Tacha los que no cumplen.`,
          draw: (ctx, box) => drawNumeral(ctx, n, box),
        })),
      },
      {
        say: 'Esta semana llovió todas las tardes. Hoy en la tarde hay nubes negras. ¿Qué es más probable?',
        ask: '¿Qué es más probable hoy?',
        hint: 'Piensa en lo que pasó los otros días y en las nubes negras.',
        choices: ['🌧️', '☀️'].map((sky, i) => ({ correct: i === 0, draw: (ctx, box) => drawEmoji(ctx, sky, box.x + box.w / 2, box.y + box.h / 2, Math.min(box.w, box.h) * 0.6) })),
      },
    ];
  }
}
