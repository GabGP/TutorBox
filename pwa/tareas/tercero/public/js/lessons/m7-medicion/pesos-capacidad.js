// Nivel 7 · Onzas, Libras, Quintales y Galones
// CNB Tercero, competencia 7 — 7.2.1 (equivalencias entre onzas, libras, arrobas y quintal), 7.2.2
// (estimar el peso), 7.3.1 (equivalencias entre vaso, botella y galón) y 7.4.1 (medidas propias
// de la región: la mano). Cada equivalencia se dice en la pregunta y la respuesta se calcula.
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { center, drawEmoji, drawText } from '../shared/draw.js';

const OZ_PER_LB = 16;
const LB_PER_ARROBA = 25;
const ARROBAS_PER_QUINTAL = 4;
const BOTTLES_PER_GALLON = 5;
const PER_MANO = 5;
// Smallest to biggest, to compare how much fits.
const CONTAINERS = ['vaso', 'botella', 'galón'];

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

function container(name) {
  return (ctx, box) => {
    const { cx, cy } = center(box);
    const s = Math.min(box.w, box.h) * (name === 'galón' ? 0.8 : name === 'botella' ? 0.6 : 0.35);
    ctx.fillStyle = '#81D4FA';
    ctx.strokeStyle = '#0277BD';
    ctx.lineWidth = 3;
    ctx.beginPath();
    if (name === 'vaso') {
      ctx.moveTo(cx - s * 0.35, cy - s * 0.45); ctx.lineTo(cx + s * 0.35, cy - s * 0.45);
      ctx.lineTo(cx + s * 0.25, cy + s * 0.45); ctx.lineTo(cx - s * 0.25, cy + s * 0.45); ctx.closePath();
    } else if (name === 'botella') {
      ctx.roundRect(cx - s * 0.2, cy - s * 0.2, s * 0.4, s * 0.65, 8);
      ctx.rect(cx - s * 0.07, cy - s * 0.42, s * 0.14, s * 0.22);
    } else {
      ctx.roundRect(cx - s * 0.35, cy - s * 0.3, s * 0.7, s * 0.72, 12);
      ctx.rect(cx - s * 0.1, cy - s * 0.44, s * 0.2, s * 0.14);
    }
    ctx.fill(); ctx.stroke();
    if (name === 'galón') { ctx.beginPath(); ctx.arc(cx + s * 0.35, cy - s * 0.05, s * 0.14, -Math.PI / 2, Math.PI / 2); ctx.stroke(); }
    drawText(ctx, name, { x: box.x, y: box.y + box.h * 0.8, w: box.w, h: box.h * 0.18 });
  };
}

const THINGS = [['costal de maíz', 100], ['lápiz', 0.02], ['carta', 0.05]];

export default class PesosCapacidadLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a pesar y medir como en el mercado!'; }
  get colors() { return ['#E1F5FE', '#FFFDE7']; }

  makeRounds() {
    const pounds = 2;
    const quintal = ARROBAS_PER_QUINTAL * LB_PER_ARROBA;
    const heaviest = THINGS.reduce((a, b) => (b[1] > a[1] ? b : a))[0];
    const gallons = 3;
    const manos = 4;
    return [
      {
        say: `Una libra tiene ${OZ_PER_LB} onzas. ¿Cuántas onzas tienen ${pounds} libras?`,
        ask: `${pounds} libras = ¿onzas?`,
        hint: `Suma ${OZ_PER_LB} onzas por cada libra.`,
        scene: (ctx, box) => [0, 1].forEach((i) => sack(ctx, box.x + box.w * (0.3 + i * 0.4), box.y + box.h / 2, Math.min(box.h * 0.8, box.w * 0.38), '1 libra')),
        choices: pickChoices(pounds * OZ_PER_LB, [pounds + OZ_PER_LB, OZ_PER_LB]),
      },
      {
        say: `Un quintal tiene ${ARROBAS_PER_QUINTAL} arrobas, y cada arroba tiene ${LB_PER_ARROBA} libras. ¿Cuántas libras tiene un quintal?`,
        ask: '1 quintal = ¿libras?',
        hint: `Son ${ARROBAS_PER_QUINTAL} veces ${LB_PER_ARROBA} libras.`,
        choices: pickChoices(quintal, [ARROBAS_PER_QUINTAL + LB_PER_ARROBA, LB_PER_ARROBA]),
      },
      {
        say: '¿Qué cosa pesarías en quintales?',
        ask: '¿Qué se pesa en quintales?',
        hint: 'Un quintal es muy pesado: son cien libras.',
        choices: THINGS.map(([name]) => ({
          value: name,
          correct: name === heaviest,
          draw: name === 'costal de maíz'
            ? (ctx, box) => sack(ctx, box.x + box.w / 2, box.y + box.h * 0.45, Math.min(box.w, box.h) * 0.8, 'maíz')
            : (ctx, box) => drawEmoji(ctx, name === 'lápiz' ? '✏️' : '✉️', box.x + box.w / 2, box.y + box.h / 2, Math.min(box.w, box.h) * 0.55),
        })),
      },
      {
        say: `Un galón de agua llena ${BOTTLES_PER_GALLON} botellas. ¿Cuántas botellas llenan ${gallons} galones?`,
        ask: `${gallons} galones = ¿botellas?`,
        hint: `Cada galón llena ${BOTTLES_PER_GALLON} botellas.`,
        choices: pickChoices(gallons * BOTTLES_PER_GALLON, [gallons + BOTTLES_PER_GALLON, BOTTLES_PER_GALLON * 2]),
      },
      {
        say: `En el mercado, una mano de elotes son ${PER_MANO} elotes. Doña Juana compró ${manos} manos. ¿Cuántos elotes compró?`,
        ask: `${manos} manos de elotes = ¿elotes?`,
        hint: `Cada mano son ${PER_MANO} elotes: cuenta de ${PER_MANO} en ${PER_MANO}.`,
        choices: pickChoices(manos * PER_MANO, [manos + PER_MANO, manos * 4]),
      },
      {
        say: '¿Dónde cabe más agua?',
        ask: '¿Dónde cabe más?',
        hint: `Un galón llena ${BOTTLES_PER_GALLON} botellas, y una botella llena varios vasos.`,
        choices: CONTAINERS.map((name) => ({ value: name, correct: name === CONTAINERS[CONTAINERS.length - 1], draw: container(name) })),
      },
    ];
  }
}
