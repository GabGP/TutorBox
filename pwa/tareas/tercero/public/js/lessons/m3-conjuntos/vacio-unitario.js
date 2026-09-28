// Nivel 3 · Conjunto Vacío y Unitario
// CNB Tercero, competencia 3 — 3.1.1 (asociación del conjunto vacío y unitario con conjuntos de su
// entorno). El tipo de conjunto se decide contando sus elementos, nunca a mano.
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { drawEmoji, drawText } from '../shared/draw.js';
import { aguacate, banano, mango, vaca } from '../shared/art.js';

export const KINDS = ['vacío', 'unitario', 'de varios'];
export const kindOf = (n) => KINDS[Math.min(n, 2)];

/** A set drawn as a rope loop with its elements inside, and an optional letter on top. */
export function drawSet(ctx, box, arts, { label = '' } = {}) {
  const { x, y, w, h } = box;
  ctx.save();
  ctx.strokeStyle = '#8D5524';
  ctx.lineWidth = 5;
  ctx.setLineDash([14, 6]);
  ctx.beginPath(); ctx.ellipse(x + w / 2, y + h / 2, w * 0.46, h * 0.42, 0, 0, Math.PI * 2); ctx.stroke();
  ctx.restore();
  if (label) drawText(ctx, label, { x: x + w * 0.02, y: y, w: w * 0.2, h: h * 0.2 }, '#8D5524');
  // As many columns as suit the box's shape: a row in a wide scene, a column in a narrow card.
  const cols = Math.max(1, Math.min(arts.length, Math.round(Math.sqrt((arts.length * w) / h))));
  const rows = Math.ceil(arts.length / cols);
  const cell = Math.min((w * 0.7) / cols, (h * 0.66) / Math.max(rows, 1));
  arts.forEach((a, i) => {
    const inRow = Math.min(cols, arts.length - Math.floor(i / cols) * cols);
    const cx = x + w / 2 + ((i % cols) - (inRow - 1) / 2) * cell;
    const cy = y + h / 2 + (Math.floor(i / cols) - (rows - 1) / 2) * cell;
    drawEmoji(ctx, a, cx, cy, cell * 0.8);
  });
}

const MONTH_DAYS = {
  enero: 31, febrero: 28, marzo: 31, abril: 30, mayo: 31, junio: 30,
  julio: 31, agosto: 31, septiembre: 30, octubre: 31, noviembre: 30, diciembre: 31,
};

function pickSet(kind, sets, say) {
  return {
    say,
    ask: `¿Cuál es un conjunto ${kind}?`,
    hint: kind === 'vacío' ? 'El conjunto vacío no tiene ningún elemento adentro.' : 'El conjunto unitario tiene un solo elemento.',
    choices: sets.map((s) => ({ correct: kindOf(s.length) === kind, draw: (ctx, box) => drawSet(ctx, box, s) })),
  };
}

function whatKind(say, elements, scene) {
  return {
    say,
    ask: '¿Qué tipo de conjunto es?',
    hint: 'Cuenta sus elementos: ninguno es vacío, uno solo es unitario.',
    scene,
    choices: pickChoices(kindOf(elements.length), KINDS),
  };
}

export default class VacioUnitarioLesson extends ChoiceLesson {
  get intro() { return '¡Hay conjuntos sin nada y conjuntos con uno solo!'; }
  get colors() { return ['#FFF3E0', '#FFFDE7']; }

  makeRounds() {
    const suns = ['☀️'];
    const flyingCows = [];
    const shortMonths = Object.keys(MONTH_DAYS).filter((m) => MONTH_DAYS[m] < 30);
    return [
      pickSet('vacío', [[], [mango], [mango, banano, aguacate]], '¿Cuál de estos es un conjunto vacío?'),
      pickSet('unitario', [[vaca], [mango, banano], []], '¿Cuál de estos es un conjunto unitario?'),
      whatKind('Este es el conjunto de los soles de nuestro cielo. ¿Qué tipo de conjunto es?', suns, (ctx, box) => drawSet(ctx, box, suns)),
      whatKind('Este es el conjunto de las vacas que vuelan. ¿Qué tipo de conjunto es?', flyingCows, (ctx, box) => drawSet(ctx, box, flyingCows)),
      whatKind('Piensa en el conjunto de los meses del año que tienen menos de 30 días. ¿Qué tipo de conjunto es?', shortMonths),
    ];
  }
}
