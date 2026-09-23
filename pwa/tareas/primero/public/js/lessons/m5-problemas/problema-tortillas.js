// Módulo 5 · Tortillas para la Familia
// CNB Primero 5.3.1 (problemas con suma o resta), 3.3.1 (uno a uno) y 4.8.1 / 4.8.6.
import { ChoiceLesson, numberChoices } from '../shared/choice-lesson.js';
import { drawEmoji, drawItems } from '../shared/draw.js';

export function drawTortilla(ctx, cx, cy, size) {
  const r = size * 0.42;
  ctx.fillStyle = '#F3DFA2';
  ctx.strokeStyle = '#C9A55C';
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.ellipse(cx, cy, r, r * 0.8, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
  ctx.fillStyle = 'rgba(141,85,36,0.45)';
  [[-0.35, -0.2], [0.3, 0.1], [-0.05, 0.35], [0.2, -0.35]].forEach(([dx, dy]) => {
    ctx.beginPath(); ctx.arc(cx + dx * r, cy + dy * r, r * 0.08, 0, Math.PI * 2); ctx.fill();
  });
}

function plate(ctx, cx, cy, r) {
  ctx.fillStyle = '#FFFFFF';
  ctx.strokeStyle = '#90A4AE';
  ctx.lineWidth = 3;
  ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
  ctx.beginPath(); ctx.arc(cx, cy, r * 0.65, 0, Math.PI * 2); ctx.stroke();
}

// Two people, each with their tortillas under them.
function twoPeople(ctx, box, [who1, n1], [who2, n2]) {
  const half = box.w / 2;
  const slots = Math.max(n1, n2);
  [[box.x, who1, n1], [box.x + half, who2, n2]].forEach(([x, who, n]) => {
    drawEmoji(ctx, who, x + half / 2, box.y + box.h * 0.2, box.h * 0.25);
    drawItems(ctx, drawTortilla, n, { x: x + half * 0.1, y: box.y + box.h * 0.38, w: half * 0.8, h: box.h * 0.58 }, { slots });
  });
}

export default class ProblemaTortillasLesson extends ChoiceLesson {
  get intro() { return '¡Es hora de comer con la familia!'; }
  get colors() { return ['#FFF8E1', '#FFE0B2']; }

  makeRounds() {
    const platos = 5;
    return [
      {
        say: 'Mamá hizo 4 tortillas y la abuela hizo 3. ¿Cuántas tortillas hay en total?',
        ask: '4 + 3 = ?',
        hint: 'Junta las tortillas de mamá y de la abuela, y cuéntalas.',
        scene: (ctx, box) => twoPeople(ctx, box, ['👩', 4], ['👵', 3]),
        choices: numberChoices(4 + 3, { max: 10 }),
      },
      {
        say: 'Había 6 tortillas. La familia se comió 4. ¿Cuántas tortillas quedan?',
        ask: '6 − 4 = ?',
        hint: 'Cuenta solo las tortillas que no tienen la cruz roja.',
        scene: (ctx, box) => drawItems(ctx, drawTortilla, 6, box, { crossed: 4 }),
        choices: numberChoices(6 - 4, { max: 10 }),
      },
      {
        say: `En la mesa hay ${platos} platos. Cada plato lleva una tortilla. ¿Cuántas tortillas necesitas?`,
        ask: 'Una tortilla en cada plato',
        hint: 'Pon con el dedo una tortilla en cada plato, y cuenta.',
        scene: (ctx, box) => {
          const cell = box.w / platos;
          for (let i = 0; i < platos; i++) plate(ctx, box.x + cell * (i + 0.5), box.y + box.h * 0.5, cell * 0.4);
        },
        choices: numberChoices(platos, { max: 10 }),
      },
      {
        say: 'Papá tiene 2 tortillas y Juan tiene 2. ¿Cuántas tortillas tienen juntos?',
        ask: '2 + 2 = ?',
        hint: 'Cuenta las tortillas de papá y luego sigue con las de Juan.',
        scene: (ctx, box) => twoPeople(ctx, box, ['👨', 2], ['👦', 2]),
        choices: numberChoices(2 + 2, { max: 10 }),
      },
    ];
  }
}
