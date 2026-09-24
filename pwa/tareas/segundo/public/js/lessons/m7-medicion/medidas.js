// Nivel 7 · Metros, Libras y Litros
// CNB Segundo, competencia 7 — 7.2.2 (estimación y medición de longitud con metro y centímetro),
// 7.1.2 (peso con onza, libra y arroba) y 7.3.1 (capacidad con vaso, botella, litro y galón).
// Distractor clave de la regla: leer el número del final cuando el objeto no empieza en el 0.
import { ChoiceLesson, numberChoices, pickChoices } from '../shared/choice-lesson.js';
import { center, drawItems, drawText } from '../shared/draw.js';

const RULER_CM = 12;
const CM_PER_M = 100;
const LB_PER_ARROBA = 25;
const OZ = { libra: 16, onza: 1 };
const GLASSES_PER_BOTTLE = 4;

function ruler(ctx, box, from, to) {
  const cm = (box.w * 0.9) / RULER_CM;
  const x0 = box.x + box.w * 0.05;
  const top = box.y + box.h * 0.55;
  ctx.save();
  ctx.fillStyle = '#FFE082';
  ctx.strokeStyle = '#8D6E63';
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.roundRect(x0 - 6, top, cm * RULER_CM + 12, box.h * 0.32, 6); ctx.fill(); ctx.stroke();
  ctx.fillStyle = '#4E342E';
  ctx.font = `bold ${Math.round(cm * 0.55)}px Nunito, sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  for (let i = 0; i <= RULER_CM; i++) {
    ctx.beginPath(); ctx.moveTo(x0 + i * cm, top); ctx.lineTo(x0 + i * cm, top + box.h * 0.1); ctx.stroke();
    ctx.fillText(String(i), x0 + i * cm, top + box.h * 0.14);
  }
  // The pencil, lying on the ruler from `from` to `to`.
  const [a, b] = [x0 + from * cm, x0 + to * cm];
  const y = top - box.h * 0.12;
  const h = box.h * 0.14;
  ctx.fillStyle = '#FDD835';
  ctx.fillRect(a, y - h / 2, b - a - h, h);
  ctx.fillStyle = '#FFCC80';
  ctx.beginPath(); ctx.moveTo(b - h, y - h / 2); ctx.lineTo(b, y); ctx.lineTo(b - h, y + h / 2); ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#F48FB1';
  ctx.fillRect(a, y - h / 2, h * 0.5, h);
  ctx.restore();
}

function sack(ctx, cx, cy, size, text) {
  ctx.save();
  ctx.fillStyle = '#D7B98E';
  ctx.strokeStyle = '#8D6E63';
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(cx - size * 0.25, cy - size * 0.4);
  ctx.quadraticCurveTo(cx - size * 0.5, cy + size * 0.45, cx, cy + size * 0.45);
  ctx.quadraticCurveTo(cx + size * 0.5, cy + size * 0.45, cx + size * 0.25, cy - size * 0.4);
  ctx.closePath(); ctx.fill(); ctx.stroke();
  ctx.restore();
  drawText(ctx, text, { x: cx - size * 0.35, y: cy - size * 0.05, w: size * 0.7, h: size * 0.35 });
}

function glass(ctx, cx, cy, size) {
  ctx.fillStyle = '#B3E5FC';
  ctx.strokeStyle = '#0277BD';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(cx - size * 0.28, cy - size * 0.35); ctx.lineTo(cx + size * 0.28, cy - size * 0.35);
  ctx.lineTo(cx + size * 0.2, cy + size * 0.35); ctx.lineTo(cx - size * 0.2, cy + size * 0.35);
  ctx.closePath(); ctx.fill(); ctx.stroke();
}

function bottle(ctx, cx, cy, size) {
  ctx.fillStyle = '#81D4FA';
  ctx.strokeStyle = '#0277BD';
  ctx.lineWidth = 3;
  ctx.beginPath(); ctx.roundRect(cx - size * 0.22, cy - size * 0.2, size * 0.44, size * 0.65, 10); ctx.fill(); ctx.stroke();
  ctx.beginPath(); ctx.rect(cx - size * 0.08, cy - size * 0.42, size * 0.16, size * 0.22); ctx.fill(); ctx.stroke();
}

const sackCard = (name, size) => (ctx, box) => {
  const { cx, cy } = center(box);
  sack(ctx, cx, cy, Math.min(box.w, box.h) * size, `1 ${name}`);
};

export default class MedidasLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a medir, pesar y llenar como en el mercado!'; }
  get colors() { return ['#E1F5FE', '#FFFDE7']; }

  makeRounds() {
    const [from, to] = [2, 9];
    const heavier = Object.keys(OZ).reduce((a, b) => (OZ[a] > OZ[b] ? a : b));
    return [
      {
        say: 'El lápiz empieza en el cero. ¿Cuántos centímetros mide?',
        ask: '¿Cuántos centímetros mide el lápiz?',
        hint: 'Mira en qué número termina la punta del lápiz.',
        scene: (ctx, box) => ruler(ctx, box, 0, to),
        choices: numberChoices(to, { max: RULER_CM }),
      },
      {
        say: 'Cuidado: este lápiz NO empieza en el cero. ¿Cuántos centímetros mide?',
        ask: '¿Cuántos centímetros mide ahora?',
        hint: `Empieza en el ${from} y termina en el ${to}. Cuenta los centímetros que hay entre ellos.`,
        scene: (ctx, box) => ruler(ctx, box, from, to),
        choices: pickChoices(to - from, [to, to + from]),
      },
      {
        say: `Un metro tiene ${CM_PER_M} centímetros. ¿Cuántos centímetros son 2 metros?`,
        ask: '2 metros = ¿cuántos centímetros?',
        hint: `Suma ${CM_PER_M} y ${CM_PER_M}.`,
        choices: pickChoices(2 * CM_PER_M, [2 + CM_PER_M, 20]),
      },
      {
        say: `En el mercado, una arroba son ${LB_PER_ARROBA} libras. ¿Cuántas libras son 2 arrobas?`,
        ask: '2 arrobas = ¿cuántas libras?',
        hint: `Cada arroba son ${LB_PER_ARROBA} libras. Suma dos veces ${LB_PER_ARROBA}.`,
        scene: (ctx, box) => {
          const size = Math.min(box.h * 0.8, box.w * 0.42);
          sack(ctx, box.x + box.w * 0.27, box.y + box.h / 2, size, '1 arroba');
          sack(ctx, box.x + box.w * 0.73, box.y + box.h / 2, size, '1 arroba');
        },
        choices: pickChoices(2 * LB_PER_ARROBA, [LB_PER_ARROBA + 2, LB_PER_ARROBA]),
      },
      {
        say: 'Con estos vasos de agua llenamos la botella de un litro. ¿Cuántos vasos caben en la botella?',
        ask: '¿Cuántos vasos llenan la botella?',
        hint: 'Cuenta los vasos, uno por uno.',
        scene: (ctx, box) => {
          drawItems(ctx, glass, GLASSES_PER_BOTTLE, { x: box.x, y: box.y, w: box.w * 0.62, h: box.h });
          bottle(ctx, box.x + box.w * 0.82, box.y + box.h * 0.55, box.h * 0.8);
        },
        choices: numberChoices(GLASSES_PER_BOTTLE, { max: 9 }),
      },
      {
        say: '¿Qué pesa MÁS: una libra de frijol o una onza de frijol?',
        ask: '¿Qué pesa más?',
        hint: 'Una libra tiene 16 onzas.',
        choices: [['libra', 0.9], ['onza', 0.5]].map(([name, size]) => ({ correct: name === heavier, draw: sackCard(name, size) })),
      },
    ];
  }
}
