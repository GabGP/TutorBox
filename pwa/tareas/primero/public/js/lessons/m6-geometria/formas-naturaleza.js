// Módulo 6 · Formas en la Naturaleza
// CNB Primero 1.4.1 (figuras geométricas en objetos del entorno) y 6.1.2 (círculos y figuras con líneas rectas).
import { ChoiceLesson } from '../shared/choice-lesson.js';
import { center, drawShape } from '../shared/draw.js';

const SHAPES = { circle: '#FB8C00', triangle: '#43A047', square: '#1E88E5' };
const NAMES = { circle: 'círculo', triangle: 'triángulo', square: 'cuadrado' };

function sun(ctx, box, t) {
  const { cx, cy } = center(box);
  const r = Math.min(box.w, box.h) * 0.22;
  ctx.strokeStyle = '#FFB300';
  ctx.lineWidth = 6;
  ctx.lineCap = 'round';
  for (let i = 0; i < 12; i++) {
    const a = (Math.PI * 2 * i) / 12 + t * 0.3;
    ctx.beginPath();
    ctx.moveTo(cx + Math.cos(a) * r * 1.25, cy + Math.sin(a) * r * 1.25);
    ctx.lineTo(cx + Math.cos(a) * r * 1.6, cy + Math.sin(a) * r * 1.6);
    ctx.stroke();
  }
  ctx.fillStyle = '#FDD835';
  ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.fill();
}

function volcano(ctx, box, t) {
  const base = box.y + box.h * 0.92;
  const w = box.w * 0.7;
  const cx = box.x + box.w / 2;
  ctx.fillStyle = `rgba(158,158,158,${0.5 + Math.sin(t * 2) * 0.15})`;
  ctx.beginPath(); ctx.arc(cx + 10, box.y + box.h * 0.14, box.h * 0.08, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#6D4C41';
  ctx.beginPath();
  ctx.moveTo(cx - w / 2, base); ctx.lineTo(cx, box.y + box.h * 0.2); ctx.lineTo(cx + w / 2, base);
  ctx.closePath(); ctx.fill();
}

function windowWall(ctx, box) {
  ctx.fillStyle = '#D7A86E';
  ctx.fillRect(box.x + box.w * 0.1, box.y + box.h * 0.08, box.w * 0.8, box.h * 0.84);
  const s = Math.min(box.w, box.h) * 0.42;
  const { cx, cy } = center(box);
  ctx.fillStyle = '#81D4FA';
  ctx.strokeStyle = '#5D4037';
  ctx.lineWidth = 8;
  ctx.fillRect(cx - s / 2, cy - s / 2, s, s);
  ctx.strokeRect(cx - s / 2, cy - s / 2, s, s);
  ctx.lineWidth = 5;
  ctx.beginPath(); ctx.moveTo(cx, cy - s / 2); ctx.lineTo(cx, cy + s / 2);
  ctx.moveTo(cx - s / 2, cy); ctx.lineTo(cx + s / 2, cy); ctx.stroke();
}

function moon(ctx, box) {
  ctx.fillStyle = '#1A237E';
  ctx.beginPath(); ctx.roundRect(box.x, box.y, box.w, box.h, 18); ctx.fill();
  const { cx, cy } = center(box);
  ctx.fillStyle = '#FFF9C4';
  ctx.beginPath(); ctx.arc(cx, cy, Math.min(box.w, box.h) * 0.25, 0, Math.PI * 2); ctx.fill();
}

const ROUNDS = [
  { thing: 'el sol', scene: sun, shape: 'circle', hint: 'Mira el borde del sol: ¿es redondo o tiene puntas?' },
  { thing: 'el volcán', scene: volcano, shape: 'triangle', hint: 'El volcán tiene una punta arriba y dos lados rectos.' },
  { thing: 'la ventana', scene: windowWall, shape: 'square', hint: 'La ventana tiene cuatro lados iguales.' },
  { thing: 'la luna llena', scene: moon, shape: 'circle', hint: 'La luna llena es redonda, sin puntas.' },
];

export default class FormasNaturalezaLesson extends ChoiceLesson {
  get intro() { return '¡Busquemos figuras a nuestro alrededor!'; }
  get colors() { return ['#E1F5FE', '#FFF8E1']; }

  makeRounds() {
    return ROUNDS.map(({ thing, scene, shape, hint }) => ({
      say: `Mira ${thing}. ¿A qué figura se parece?`,
      ask: `¿Qué figura es ${thing}?`,
      hint,
      scene,
      choices: Object.keys(SHAPES).map((kind) => ({
        correct: kind === shape,
        hint: kind === shape ? undefined : `Ese es un ${NAMES[kind]}. ${hint}`,
        draw: (ctx, box) => drawShape(ctx, kind, box.x + box.w / 2, box.y + box.h / 2, Math.min(box.w, box.h) * 0.36, SHAPES[kind]),
      })),
    }));
  }
}
