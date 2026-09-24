// Nivel 6 · Figuras Simétricas
// CNB Segundo, competencia 6 — 6.5.1 (elaboración de manualidades con figuras simétricas).
// Completar el otro lado del tejido: la respuesta es el reflejo en el espejo; los distractores son
// la misma mitad sin reflejar y el reflejo de cabeza. Todo se calcula desde las casillas.
import { ChoiceLesson, stacked } from '../shared/choice-lesson.js';

const HALF_W = 3;
const H = 4;
const COLOR = '#C2185B';

const mirror = (cells) => cells.map(([x, y]) => [HALF_W - 1 - x, y]);
const upsideDown = (cells) => mirror(cells).map(([x, y]) => [x, H - 1 - y]);
const key = (cells) => cells.map(([x, y]) => `${x}${y}`).sort().join(' ');
const whole = (left, right) => [...left, ...right.map(([x, y]) => [x + HALF_W, y])];
const isSymmetric = (cells) => {
  const all = new Set(cells.map(([x, y]) => `${x},${y}`));
  return cells.every(([x, y]) => all.has(`${2 * HALF_W - 1 - x},${y}`));
};

function grid(ctx, box, cols, cells, { mirrorLine = false } = {}) {
  const c = Math.min(box.w / cols, box.h / H);
  const x0 = box.x + (box.w - c * cols) / 2;
  const y0 = box.y + (box.h - c * H) / 2;
  ctx.save();
  ctx.strokeStyle = 'rgba(0,0,0,0.15)';
  ctx.lineWidth = 1;
  for (let x = 0; x < cols; x++) for (let y = 0; y < H; y++) ctx.strokeRect(x0 + x * c, y0 + y * c, c, c);
  ctx.fillStyle = COLOR;
  cells.forEach(([x, y]) => ctx.fillRect(x0 + x * c + 1, y0 + y * c + 1, c - 2, c - 2));
  if (mirrorLine) {
    ctx.setLineDash([8, 6]);
    ctx.strokeStyle = '#1565C0';
    ctx.lineWidth = 4;
    ctx.beginPath(); ctx.moveTo(x0 + HALF_W * c, y0 - 6); ctx.lineTo(x0 + HALF_W * c, y0 + H * c + 6); ctx.stroke();
  }
  ctx.restore();
}

const HALVES = [
  [[0, 0], [1, 0], [1, 1], [2, 1], [2, 2], [2, 3]],
  [[0, 0], [0, 1], [0, 2], [0, 3], [1, 3], [2, 3]],
  [[2, 0], [1, 1], [2, 1], [0, 2], [1, 2], [2, 2], [2, 3]],
];

function complete(left) {
  const right = mirror(left);
  return {
    say: 'La línea azul es un espejo. ¿Qué mitad completa el tejido para que los dos lados sean iguales?',
    ask: '¿Qué mitad completa el tejido?',
    hint: 'Del otro lado del espejo todo se ve al revés: lo que está pegado a la línea sigue pegado a la línea.',
    scene: (ctx, box) => grid(ctx, box, HALF_W * 2, left, { mirrorLine: true }),
    choices: [right, left, upsideDown(left)].map((cells) => ({
      value: key(cells),
      correct: key(cells) === key(right),
      draw: (ctx, box) => grid(ctx, box, HALF_W, cells),
    })),
  };
}

export default class SimetriaLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a tejer figuras simétricas, iguales de los dos lados!'; }
  get colors() { return ['#FFEBEE', '#F3E5F5']; }

  makeRounds() {
    // Stacked cards are not shuffled: the symmetric design sits in the middle.
    const designs = [whole(HALVES[0], HALVES[0]), whole(HALVES[0], mirror(HALVES[0])), whole(HALVES[1], upsideDown(HALVES[1]))];
    return [
      ...HALVES.map(complete),
      {
        say: '¿Cuál de estos tejidos es simétrico? Si lo doblas por la mitad, los dos lados coinciden.',
        ask: '¿Cuál tejido es simétrico?',
        hint: 'Imagina un espejo en medio. ¿Cuál se ve igual de los dos lados?',
        choices: stacked(designs.map((cells) => ({
          value: key(cells),
          correct: isSymmetric(cells),
          draw: (ctx, box) => grid(ctx, box, HALF_W * 2, cells),
        }))),
      },
    ];
  }
}
