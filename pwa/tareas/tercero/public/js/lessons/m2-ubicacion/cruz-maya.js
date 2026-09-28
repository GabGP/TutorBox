// Nivel 2 · La Cruz Maya
// CNB Tercero, competencia 2 — 2.1.3 (relación de los puntos cardinales con la Cruz Maya) y 2.1.1
// (signos y señales que indican desplazamientos). Dibujada con el Norte arriba, como en los mapas:
// Este rojo (sale el sol), Oeste negro (se oculta), Norte blanco, Sur amarillo y el centro verde.
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { center, drawEmoji, drawText } from '../shared/draw.js';

// On screen x grows to the right and y grows down, so the Norte (up) is dy = -1.
const POINTS = [
  { name: 'Este', color: '#D32F2F', word: 'rojo', dx: 1, dy: 0 },
  { name: 'Oeste', color: '#212121', word: 'negro', dx: -1, dy: 0 },
  { name: 'Norte', color: '#FAFAFA', word: 'blanco', dx: 0, dy: -1 },
  { name: 'Sur', color: '#FDD835', word: 'amarillo', dx: 0, dy: 1 },
];
const point = (name) => POINTS.find((p) => p.name === name);
// What is on your left when you face `p`.
const leftOf = (p) => POINTS.find((q) => q.dx === p.dy && q.dy === -p.dx);

function disc(ctx, x, y, r, color) {
  ctx.fillStyle = color;
  ctx.strokeStyle = '#5D4037';
  ctx.lineWidth = 3;
  ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
}

function cross(ctx, box, { sun = null, north = false } = {}) {
  const { cx, cy } = center(box);
  const r = Math.min(box.w, box.h) * 0.1;
  const arm = r * 2.3;
  ctx.strokeStyle = '#5D4037';
  ctx.lineWidth = r * 0.5;
  ctx.beginPath(); ctx.moveTo(cx - arm, cy); ctx.lineTo(cx + arm, cy); ctx.moveTo(cx, cy - arm); ctx.lineTo(cx, cy + arm); ctx.stroke();
  POINTS.forEach((p) => disc(ctx, cx + p.dx * arm, cy + p.dy * arm, r, p.color));
  disc(ctx, cx, cy, r * 0.8, '#43A047');
  if (sun) {
    const p = point(sun);
    drawEmoji(ctx, '☀️', cx + p.dx * arm * 1.8, cy + p.dy * arm * 1.8, r * 1.4);
  }
  if (north) drawText(ctx, 'N', { x: cx - r, y: cy - arm - r * 2.4, w: r * 2, h: r * 1.2 }, '#1565C0');
}

const swatch = (p) => ({ value: p.word, draw: (ctx, box) => { const { cx, cy } = center(box); disc(ctx, cx, cy, Math.min(box.w, box.h) * 0.3, p.color); } });

function arrow(p) {
  return (ctx, box) => {
    const { cx, cy } = center(box);
    const len = Math.min(box.w, box.h) * 0.32;
    const [tx, ty] = [cx + p.dx * len, cy + p.dy * len];
    ctx.strokeStyle = '#1565C0';
    ctx.fillStyle = '#1565C0';
    ctx.lineWidth = 7;
    ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(cx - p.dx * len, cy - p.dy * len); ctx.lineTo(tx, ty); ctx.stroke();
    const [nx, ny] = [-p.dy, p.dx];
    ctx.beginPath();
    ctx.moveTo(tx + p.dx * 14, ty + p.dy * 14);
    ctx.lineTo(tx + nx * 12, ty + ny * 12);
    ctx.lineTo(tx - nx * 12, ty - ny * 12);
    ctx.closePath(); ctx.fill();
  };
}

function colorOf(name, say, others, scene, hint) {
  const answer = point(name);
  return {
    say,
    ask: `¿De qué color es el ${name}?`,
    hint,
    scene,
    choices: [answer, ...others.map(point)].map((p) => ({ ...swatch(p), correct: p === answer })),
  };
}

export default class CruzMayaLesson extends ChoiceLesson {
  get intro() { return '¡Los abuelos mayas ubicaban los puntos cardinales con colores!'; }
  get colors() { return ['#E8F5E9', '#FFF8E1']; }

  makeRounds() {
    const facing = point('Este');
    const south = point('Sur');
    return [
      colorOf('Este', 'El sol sale por el Este. En la Cruz Maya, ¿de qué color es el Este?', ['Oeste', 'Sur'],
        (ctx, box) => cross(ctx, box, { sun: 'Este' }), 'Mira qué color está junto al sol que sale.'),
      colorOf('Oeste', 'El Norte está arriba. El sol se oculta por el Oeste, del otro lado del Este. ¿De qué color es el Oeste?', ['Este', 'Norte'],
        (ctx, box) => cross(ctx, box, { north: true }), 'El Oeste está a la izquierda cuando el Norte está arriba.'),
      colorOf('Sur', 'Con el Norte arriba, ¿de qué color es el Sur?', ['Norte', 'Este'],
        (ctx, box) => cross(ctx, box, { north: true }), 'El Sur está abajo, al otro lado del Norte.'),
      {
        say: 'Párate mirando hacia donde sale el sol, al Este. ¿Qué punto cardinal queda a tu izquierda?',
        ask: '¿Qué queda a tu izquierda?',
        hint: 'Mirando al Este, tu brazo izquierdo apunta hacia arriba en el mapa.',
        scene: (ctx, box) => cross(ctx, box, { sun: 'Este', north: true }),
        choices: pickChoices(leftOf(facing).name, ['Sur', 'Oeste']),
      },
      {
        say: 'Esta señal dice: camina hacia el Sur. Con el Norte arriba, ¿qué flecha lo muestra?',
        ask: '¿Qué flecha apunta al Sur?',
        hint: 'En el mapa, el Sur está abajo.',
        choices: [south, point('Norte'), point('Este')].map((p) => ({ value: p.name, correct: p === south, draw: arrow(p) })),
      },
    ];
  }
}
