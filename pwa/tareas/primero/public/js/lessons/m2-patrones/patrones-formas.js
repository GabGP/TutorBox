// Módulo 2 · Patrones de Formas
// CNB Primero 2.1.2 (patrones por color, forma o tamaño) y 2.2.1 (patrones en las artesanías: el güipil).
import { ChoiceLesson } from '../shared/choice-lesson.js';
import { drawShape } from '../shared/draw.js';

const RED = '#E53935';
const BLUE = '#1E88E5';
const YELLOW = '#FDD835';
const GREEN = '#43A047';
const P = (kind, color, word, size = 1) => ({ kind, color, word, size });

// The band shows five pieces of the repeating unit; the child picks the sixth.
const PATTERNS = [
  {
    unit: [P('circle', RED, 'círculo'), P('triangle', YELLOW, 'triángulo')],
    others: [P('circle', RED, ''), P('square', BLUE, '')],
  },
  {
    unit: [P('square', RED, 'rojo'), P('square', BLUE, 'azul')],
    others: [P('square', RED, ''), P('circle', YELLOW, '')],
  },
  {
    unit: [P('triangle', GREEN, 'triángulo'), P('triangle', GREEN, 'triángulo'), P('circle', BLUE, 'círculo')],
    others: [P('triangle', GREEN, ''), P('square', RED, '')],
  },
  {
    unit: [P('circle', YELLOW, 'grande', 1), P('circle', YELLOW, 'pequeño', 0.55)],
    others: [P('circle', YELLOW, '', 1), P('triangle', BLUE, '', 0.55)],
  },
];

const piece = (p) => (ctx, box) => {
  const r = Math.min(box.w, box.h) * 0.38 * p.size;
  drawShape(ctx, p.kind, box.x + box.w / 2, box.y + box.h / 2, r, p.color);
};

function band(ctx, box, seq, t) {
  const top = box.y + box.h * 0.22;
  const h = box.h * 0.56;
  ctx.fillStyle = '#6A1B9A';
  ctx.beginPath(); ctx.roundRect(box.x, top, box.w, h, 12); ctx.fill();
  // Woven zigzag borders, like the edge of a güipil.
  ctx.strokeStyle = '#FFB300';
  ctx.lineWidth = 3;
  for (const y of [top + 8, top + h - 8]) {
    ctx.beginPath();
    for (let x = box.x + 6, up = true; x <= box.x + box.w - 6; x += 10, up = !up) {
      ctx.lineTo(x, y + (up ? -4 : 4));
    }
    ctx.stroke();
  }
  const cell = box.w / (seq.length + 1);
  seq.forEach((p, i) => piece(p)(ctx, { x: box.x + cell * i, y: top, w: cell, h }));
  const slot = { x: box.x + cell * seq.length + 4, y: top + 14, w: cell - 8, h: h - 28 };
  ctx.save();
  ctx.setLineDash([6, 5]);
  ctx.strokeStyle = `rgba(255,255,255,${0.6 + Math.sin(t * 4) * 0.4})`;
  ctx.lineWidth = 3;
  ctx.beginPath(); ctx.roundRect(slot.x, slot.y, slot.w, slot.h, 8); ctx.stroke();
  ctx.restore();
}

export default class PatronesFormasLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a tejer un güipil!'; }
  get colors() { return ['#F3E5F5', '#FFF8E1']; }

  makeRounds() {
    return PATTERNS.map(({ unit, others }) => {
      const seq = [0, 1, 2, 3, 4].map((i) => unit[i % unit.length]);
      const next = unit[5 % unit.length];
      const words = seq.map((p) => p.word).join(', ');
      return {
        say: `Mira el tejido: ${words}... ¿Qué sigue?`,
        ask: '¿Qué pieza sigue en el güipil?',
        hint: 'Di el patrón en voz alta, desde el principio.',
        scene: (ctx, box, t) => band(ctx, box, seq, t),
        choices: [
          { correct: true, draw: piece(next) },
          ...others.map((p) => ({ correct: false, draw: piece(p) })),
        ],
      };
    });
  }
}
