// Módulo 2 · Patrones de la Naturaleza
// CNB Primero, competencia 2 — 2.1.1: identificación de patrones en objetos y fenómenos naturales.
import { ChoiceLesson } from '../shared/choice-lesson.js';
import { drawEmoji } from '../shared/draw.js';

const E = (emoji, word, size = 1) => ({ emoji, word, size });

// Each row shows five pieces of a repeating unit; the child picks the sixth, unit[5 % length].
const ROWS = [
  {
    what: 'el cielo',
    unit: [E('☀️', 'sol'), E('🌙', 'luna')],
    wrong: [E('☀️', ''), E('⭐', '')],
    hint: 'Después del sol viene la luna, y después de la luna, el sol.',
  },
  {
    what: 'las hojas',
    unit: [E('🍃', 'grande', 1), E('🍃', 'pequeña', 0.55), E('🍃', 'pequeña', 0.55)],
    wrong: [E('🍃', '', 1), E('🌸', '', 0.55)],
    hint: 'Di los tamaños en voz alta: grande, pequeña, pequeña...',
  },
  {
    what: 'la luna',
    unit: [E('🌑', 'luna nueva'), E('🌓', 'media luna'), E('🌕', 'luna llena')],
    wrong: [E('🌑', ''), E('🌓', '')],
    hint: 'La luna crece: nueva, media, llena. Y vuelve a empezar.',
  },
];

const piece = (p) => (ctx, box) => {
  drawEmoji(ctx, p.emoji, box.x + box.w / 2, box.y + box.h / 2, Math.min(box.w, box.h) * 0.75 * p.size);
};

function row(ctx, box, seq, t) {
  const top = box.y + box.h * 0.25;
  const h = box.h * 0.5;
  ctx.fillStyle = '#C8E6C9';
  ctx.beginPath(); ctx.roundRect(box.x, top, box.w, h, 14); ctx.fill();
  const cell = box.w / (seq.length + 1);
  seq.forEach((p, i) => piece(p)(ctx, { x: box.x + cell * i, y: top, w: cell, h }));
  ctx.save();
  ctx.setLineDash([6, 5]);
  ctx.strokeStyle = `rgba(46,125,50,${0.6 + Math.sin(t * 4) * 0.4})`;
  ctx.lineWidth = 3;
  ctx.beginPath(); ctx.roundRect(box.x + cell * seq.length + 4, top + 10, cell - 8, h - 20, 8); ctx.stroke();
  ctx.restore();
}

// Flower with alternating petal colours and one missing petal (dashed).
const PETALS = ['#E53935', '#FDD835'];
const PETAL_COUNT = 8;
const MISSING = 5;

function flower(ctx, box, t) {
  const cx = box.x + box.w / 2;
  const cy = box.y + box.h / 2;
  const r = Math.min(box.w, box.h) * 0.3;
  for (let i = 0; i < PETAL_COUNT; i++) {
    const a = (Math.PI * 2 * i) / PETAL_COUNT;
    ctx.save();
    ctx.translate(cx + Math.cos(a) * r, cy + Math.sin(a) * r);
    ctx.rotate(a);
    ctx.beginPath(); ctx.ellipse(0, 0, r * 0.55, r * 0.32, 0, 0, Math.PI * 2);
    if (i === MISSING) {
      ctx.setLineDash([5, 4]);
      ctx.strokeStyle = `rgba(0,0,0,${0.4 + Math.sin(t * 4) * 0.3})`;
      ctx.lineWidth = 3;
      ctx.stroke();
    } else {
      ctx.fillStyle = PETALS[i % PETALS.length];
      ctx.fill();
    }
    ctx.restore();
  }
  ctx.fillStyle = '#6D4C41';
  ctx.beginPath(); ctx.arc(cx, cy, r * 0.4, 0, Math.PI * 2); ctx.fill();
}

const petal = (color) => (ctx, box) => {
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.ellipse(box.x + box.w / 2, box.y + box.h / 2, Math.min(box.w, box.h) * 0.4, Math.min(box.w, box.h) * 0.24, 0, 0, Math.PI * 2);
  ctx.fill();
};

export default class PatronesNaturalezaLesson extends ChoiceLesson {
  get intro() { return '¡La naturaleza también tiene patrones!'; }
  get colors() { return ['#E1F5FE', '#DCEDC8']; }

  makeRounds() {
    const rows = ROWS.map(({ what, unit, wrong, hint }) => {
      const seq = [0, 1, 2, 3, 4].map((i) => unit[i % unit.length]);
      return {
        say: `Mira ${what}: ${seq.map((p) => p.word).join(', ')}... ¿Qué sigue?`,
        ask: `¿Qué sigue en ${what}?`,
        hint,
        scene: (ctx, box, t) => row(ctx, box, seq, t),
        choices: [
          { correct: true, draw: piece(unit[5 % unit.length]) },
          ...wrong.map((p) => ({ correct: false, draw: piece(p) })),
        ],
      };
    });
    const missingColor = PETALS[MISSING % PETALS.length];
    return [
      ...rows,
      {
        say: 'Mira la flor: sus pétalos son rojo, amarillo, rojo, amarillo... Falta un pétalo. ¿De qué color es?',
        ask: '¿De qué color es el pétalo que falta?',
        hint: 'Mira los pétalos que están a cada lado del que falta.',
        scene: flower,
        choices: ['#E53935', '#FDD835', '#1E88E5'].map((color) => ({ correct: color === missingColor, draw: petal(color) })),
      },
    ];
  }
}
