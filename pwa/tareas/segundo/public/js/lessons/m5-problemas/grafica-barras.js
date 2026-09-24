// Nivel 5 · La Encuesta y la Gráfica de Barras
// CNB Segundo, competencia 5 — 5.4.3 (tablas estadísticas y gráficas de barras), 5.4.2
// (encuestas para recolectar información) y 5.4.4 (comprobar supuestos con la información).
// Todas las respuestas se sacan de los datos de la encuesta, no se escriben a mano.
import { ChoiceLesson, numberChoices, pickChoices } from '../shared/choice-lesson.js';
import { drawEmoji, drawText } from '../shared/draw.js';
import { aguacate, banano, cerdo, gallina, mango, vaca } from '../shared/art.js';

const FRUITS = [[mango, 7, '#FFB300'], [banano, 4, '#FDD835'], [aguacate, 5, '#7CB342']];
const ANIMALS = [[gallina, 3, '#8D6E63'], [vaca, 5, '#78909C'], [cerdo, 2, '#F48FB1']];
const TOP = 8;

/** Bars on a 0..TOP scale with numbered gridlines; the item picture under each bar. */
function barChart(ctx, box, data, { labels = true } = {}) {
  const left = box.x + (labels ? box.w * 0.1 : box.w * 0.04);
  const bottom = box.y + box.h * 0.8;
  const unit = (box.h * 0.74) / TOP;
  const colW = (box.x + box.w - left) / data.length;
  ctx.save();
  ctx.lineWidth = 1;
  ctx.strokeStyle = 'rgba(0,0,0,0.15)';
  ctx.fillStyle = '#37474F';
  ctx.font = `bold ${Math.round(unit * 0.75)}px Nunito, sans-serif`;
  ctx.textAlign = 'right';
  ctx.textBaseline = 'middle';
  for (let v = 0; v <= TOP; v++) {
    ctx.beginPath(); ctx.moveTo(left, bottom - v * unit); ctx.lineTo(box.x + box.w, bottom - v * unit); ctx.stroke();
    if (labels) ctx.fillText(String(v), left - 4, bottom - v * unit);
  }
  data.forEach(([art, n, color], i) => {
    const x = left + colW * (i + 0.2);
    ctx.fillStyle = color;
    ctx.fillRect(x, bottom - n * unit, colW * 0.6, n * unit);
    drawEmoji(ctx, art, x + colW * 0.3, bottom + box.h * 0.1, Math.min(colW * 0.5, box.h * 0.18));
  });
  ctx.restore();
}

/** Tally marks: groups of five (four sticks and one across). */
function tally(ctx, box, data) {
  const rowH = box.h / data.length;
  data.forEach(([art, n], r) => {
    const y = box.y + rowH * (r + 0.5);
    drawEmoji(ctx, art, box.x + rowH * 0.5, y, rowH * 0.7);
    ctx.strokeStyle = '#37474F';
    ctx.lineWidth = 3;
    for (let i = 0; i < n; i++) {
      const x = box.x + rowH * 1.3 + Math.floor(i / 5) * rowH * 1.2 + (i % 5) * rowH * 0.2;
      ctx.beginPath();
      if (i % 5 === 4) { ctx.moveTo(x - rowH * 0.85, y + rowH * 0.25); ctx.lineTo(x, y - rowH * 0.25); }
      else { ctx.moveTo(x, y - rowH * 0.3); ctx.lineTo(x, y + rowH * 0.3); }
      ctx.stroke();
    }
  });
}

const scene = (ctx, box) => barChart(ctx, box, FRUITS);
const count = (art) => FRUITS.find(([a]) => a === art)[1];
const favorite = FRUITS.reduce((best, f) => (f[1] > best[1] ? f : best))[0];
const art = (a) => (ctx, box) => drawEmoji(ctx, a, box.x + box.w / 2, box.y + box.h / 2, Math.min(box.w, box.h) * 0.75);

export default class GraficaBarrasLesson extends ChoiceLesson {
  get intro() { return '¡Preguntamos a los niños de segundo qué fruta les gusta más!'; }
  get colors() { return ['#EFEBE9', '#F1F8E9']; }

  makeRounds() {
    const total = FRUITS.reduce((sum, [, n]) => sum + n, 0);
    const swapped = ANIMALS.map(([a, , c], i) => [a, ANIMALS[(i + 1) % ANIMALS.length][1], c]);
    const guessed = banano;
    return [
      {
        say: 'Esta gráfica de barras muestra la encuesta. ¿Cuántos niños eligieron el aguacate?',
        ask: '¿Cuántos eligieron aguacate?',
        hint: 'Sigue la parte de arriba de la barra verde del aguacate hasta los números de la izquierda.',
        scene,
        choices: numberChoices(count(aguacate), { max: TOP }),
      },
      {
        say: '¿Qué fruta eligieron MÁS niños?',
        ask: '¿Qué fruta eligieron más niños?',
        hint: 'La barra más alta es la que tiene más.',
        scene,
        choices: FRUITS.map(([a]) => ({ correct: a === favorite, draw: art(a) })),
      },
      {
        say: '¿Cuántos niños MÁS eligieron mango que banano?',
        ask: '¿Cuántos más mango que banano?',
        hint: 'Resta: los del mango menos los del banano.',
        scene,
        choices: pickChoices(count(mango) - count(banano), [count(mango) + count(banano), count(banano)]),
      },
      {
        say: 'La maestra pensó que el banano era la fruta favorita. Mira la gráfica. ¿Tenía razón?',
        ask: '¿El banano es la favorita?',
        hint: 'Busca la barra más alta. ¿Es la del banano?',
        scene,
        choices: [['sí', '✅'], ['no', '❌']].map(([value, mark]) => ({
          value,
          correct: (value === 'sí') === (guessed === favorite),
          draw: (ctx, box) => drawText(ctx, mark, box),
        })),
      },
      {
        say: '¿Cuántos niños contestaron la encuesta en total?',
        ask: '¿Cuántos niños contestaron?',
        hint: 'Suma lo que mide cada barra.',
        scene,
        choices: numberChoices(total, { max: 30 }),
      },
      {
        say: 'Contamos los animales de la granja con palitos. ¿Qué gráfica muestra lo que contamos?',
        ask: '¿Qué gráfica muestra estos palitos?',
        hint: 'Cuenta los palitos de cada animal y busca las barras de ese tamaño.',
        scene: (ctx, box) => tally(ctx, box, ANIMALS),
        choices: [ANIMALS, swapped].map((data, i) => ({ correct: i === 0, draw: (ctx, box) => barChart(ctx, box, data, { labels: false }) })),
      },
    ];
  }
}
