// Nivel 1 · Patrones del Tejido
// CNB Segundo, competencia 1 — 1.2.2 (diseños con patrones geométricos) y 1.2.1 (crear patrones).
// Segundo grado: el patrón se repite cada 3 piezas y puede cambiar forma, color o tamaño.
import { ChoiceLesson } from '../shared/choice-lesson.js';
import { drawShape } from '../shared/draw.js';

const RED = '#E53935';
const BLUE = '#1E88E5';
const YELLOW = '#FDD835';
const GREEN = '#43A047';
const P = (kind, color, word, size = 1) => ({ kind, color, word, size });

// The band shows SHOWN pieces of the repeating unit; the child picks the next one.
const SHOWN = 7;
const PATTERNS = [
  {
    unit: [P('circle', RED, 'círculo'), P('triangle', YELLOW, 'triángulo'), P('square', BLUE, 'cuadrado')],
    others: [P('circle', RED), P('square', BLUE)],
  },
  {
    unit: [P('square', RED, 'rojo'), P('square', RED, 'rojo'), P('square', GREEN, 'verde')],
    others: [P('square', GREEN), P('triangle', BLUE)],
  },
  {
    unit: [P('triangle', BLUE, 'triángulo'), P('circle', YELLOW, 'círculo'), P('circle', YELLOW, 'círculo')],
    others: [P('triangle', BLUE), P('square', RED)],
  },
  {
    unit: [P('circle', RED, 'grande rojo', 1), P('circle', RED, 'pequeño rojo', 0.55), P('circle', BLUE, 'grande azul', 1)],
    others: [P('circle', RED, '', 1), P('circle', BLUE, '', 0.55)],
  },
];

const piece = (p) => (ctx, box) => {
  const r = Math.min(box.w, box.h) * 0.38 * p.size;
  drawShape(ctx, p.kind, box.x + box.w / 2, box.y + box.h / 2, r, p.color);
};

function band(ctx, box, seq, t) {
  const top = box.y + box.h * 0.25;
  const h = box.h * 0.5;
  ctx.fillStyle = '#6A1B9A';
  ctx.beginPath(); ctx.roundRect(box.x, top, box.w, h, 12); ctx.fill();
  // Woven zigzag borders, like the edge of a güipil.
  ctx.strokeStyle = '#FFB300';
  ctx.lineWidth = 3;
  for (const y of [top + 8, top + h - 8]) {
    ctx.beginPath();
    for (let x = box.x + 6, up = true; x <= box.x + box.w - 6; x += 10, up = !up) ctx.lineTo(x, y + (up ? -4 : 4));
    ctx.stroke();
  }
  const cell = box.w / (seq.length + 1);
  seq.forEach((p, i) => piece(p)(ctx, { x: box.x + cell * i, y: top + 10, w: cell, h: h - 20 }));
  const slot = { x: box.x + cell * seq.length + 3, y: top + 14, w: cell - 6, h: h - 28 };
  ctx.save();
  ctx.setLineDash([6, 5]);
  ctx.strokeStyle = `rgba(255,255,255,${0.6 + Math.sin(t * 4) * 0.4})`;
  ctx.lineWidth = 3;
  ctx.beginPath(); ctx.roundRect(slot.x, slot.y, slot.w, slot.h, 8); ctx.stroke();
  ctx.restore();
}

export default class PatronesTejidoLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a tejer como las tejedoras mayas!'; }
  get colors() { return ['#F3E5F5', '#FFF8E1']; }

  makeRounds() {
    return PATTERNS.map(({ unit, others }) => {
      const seq = Array.from({ length: SHOWN }, (_, i) => unit[i % unit.length]);
      const next = unit[SHOWN % unit.length];
      return {
        say: `El patrón se repite cada ${unit.length} piezas: ${unit.map((p) => p.word).join(', ')}. ¿Qué pieza sigue?`,
        ask: '¿Qué pieza sigue en el tejido?',
        hint: 'Busca dónde empieza a repetirse y sigue contando desde ahí.',
        scene: (ctx, box, t) => band(ctx, box, seq, t),
        choices: [
          { correct: true, draw: piece(next) },
          ...others.map((p) => ({ correct: false, draw: piece(p) })),
        ],
      };
    });
  }
}
