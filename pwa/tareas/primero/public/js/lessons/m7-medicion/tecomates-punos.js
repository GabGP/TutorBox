// Módulo 7 · Tecomates y Puños
// CNB Primero, competencia 7 — 7.1.1: unidades no estándar de peso y capacidad
// (tecomate, cubeta, puño, manojo, tercio).
import { ChoiceLesson, numberChoices } from '../shared/choice-lesson.js';
import { drawItems } from '../shared/draw.js';

export function drawTecomate(ctx, cx, cy, size) {
  const r = size * 0.3;
  ctx.fillStyle = '#C8A165';
  ctx.strokeStyle = '#7B5B2E';
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.arc(cx, cy + r * 0.45, r, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
  ctx.beginPath(); ctx.arc(cx, cy - r * 0.75, r * 0.55, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
  ctx.fillStyle = '#5D4037';
  ctx.fillRect(cx - r * 0.12, cy - r * 1.5, r * 0.24, r * 0.35);
}

export function drawCubeta(ctx, cx, cy, size) {
  const w = size * 0.8;
  const h = size * 0.7;
  const top = cy - h / 2;
  ctx.strokeStyle = '#546E7A';
  ctx.lineWidth = 3;
  ctx.beginPath(); ctx.arc(cx, top, w * 0.45, Math.PI, 0); ctx.stroke();
  ctx.fillStyle = '#90A4AE';
  ctx.beginPath();
  ctx.moveTo(cx - w / 2, top); ctx.lineTo(cx + w / 2, top);
  ctx.lineTo(cx + w * 0.38, top + h); ctx.lineTo(cx - w * 0.38, top + h);
  ctx.closePath(); ctx.fill(); ctx.stroke();
  ctx.fillStyle = '#4FC3F7';
  ctx.fillRect(cx - w * 0.44, top + 3, w * 0.88, h * 0.18);
}

function drawTercio(ctx, cx, cy, size) {
  ctx.strokeStyle = '#8D5524';
  ctx.lineCap = 'round';
  ctx.lineWidth = Math.max(3, size * 0.07);
  for (let i = -2; i <= 2; i++) {
    ctx.beginPath(); ctx.moveTo(cx + i * size * 0.08, cy - size * 0.35); ctx.lineTo(cx + i * size * 0.06, cy + size * 0.35); ctx.stroke();
  }
  ctx.strokeStyle = '#FDD835';
  ctx.lineWidth = Math.max(2, size * 0.05);
  ctx.beginPath(); ctx.moveTo(cx - size * 0.22, cy); ctx.lineTo(cx + size * 0.22, cy); ctx.stroke();
}

const card = (draw, correct, hint) => ({
  correct,
  hint,
  draw: (ctx, box) => draw(ctx, box.x + box.w / 2, box.y + box.h / 2, Math.min(box.w, box.h) * 0.9),
});

export default class TecomatesPunosLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a medir como en casa, con tecomates y puños!'; }
  get colors() { return ['#FFF8E1', '#E0F2F1']; }

  makeRounds() {
    const [tecomates, punos, tercios] = [5, 4, 3];
    return [
      {
        say: 'Doña Ana llenó la cubeta con agua. Usó estos tecomates. ¿Cuántos tecomates de agua caben en la cubeta?',
        ask: '¿Cuántos tecomates caben en la cubeta?',
        hint: 'Cuenta los tecomates, uno por uno.',
        scene: (ctx, box) => {
          drawItems(ctx, drawTecomate, tecomates, { x: box.x, y: box.y, w: box.w * 0.62, h: box.h });
          drawCubeta(ctx, box.x + box.w * 0.82, box.y + box.h * 0.55, box.w * 0.3);
        },
        choices: numberChoices(tecomates, { max: 9 }),
      },
      {
        say: '¿Dónde cabe MÁS agua: en la cubeta o en el tecomate?',
        ask: '¿Dónde cabe más agua?',
        choices: [
          card(drawCubeta, true),
          card(drawTecomate, false, 'En el tecomate cabe poquita agua. Varios tecomates llenan una cubeta.'),
        ],
      },
      {
        say: 'Para hacer tortillas, mamá echó puños de maíz en la olla. ¿Cuántos puños echó?',
        ask: '¿Cuántos puños de maíz?',
        hint: 'Cuenta las manos, una por una.',
        scene: (ctx, box) => drawItems(ctx, '✊', punos, box),
        choices: numberChoices(punos, { max: 9 }),
      },
      {
        say: 'Don Pedro trajo leña en tercios. Un tercio es un manojo grande de leña amarrada. ¿Cuántos tercios trajo?',
        ask: '¿Cuántos tercios de leña?',
        hint: 'Cada manojo amarrado es un tercio. Cuéntalos.',
        scene: (ctx, box) => drawItems(ctx, drawTercio, tercios, box),
        choices: numberChoices(tercios, { max: 9 }),
      },
    ];
  }
}
