// Nivel 5 · Pictogramas y Gráficas de Barras
// CNB Tercero, competencia 5 — 5.1.2 (presentación e interpretación de información en gráficas de
// barras o pictogramas) y 5.1.1 (medios para recoger información). Distractor clave: contar los
// dibujos del pictograma sin usar la clave (cada dibujo vale 2 niños).
import { ChoiceLesson, pickChoices, stacked } from '../shared/choice-lesson.js';
import { drawEmoji, drawText } from '../shared/draw.js';
import { aguacate, banano, cerdo, gallina, mango, vaca } from '../shared/art.js';

const KEY = 2;
const FACE = '😀';
const FAVORITES = [[mango, 8], [banano, 5], [aguacate, 6]];
const VOTES = [[gallina, 12, '#8D6E63'], [vaca, 15, '#78909C'], [cerdo, 7, '#F48FB1']];
const TOP = 20;

/** One row per item: its picture, then `icons` faces (a half face for .5). */
function pictogram(ctx, box, rows, { legend = true } = {}) {
  const lines = rows.length + (legend ? 1 : 0);
  const rh = box.h / lines;
  const size = Math.min(rh * 0.8, box.w / 8.5);
  rows.forEach(([art, icons], r) => {
    const y = box.y + rh * (r + 0.5);
    drawEmoji(ctx, art, box.x + size * 0.7, y, size);
    for (let i = 0; i < Math.ceil(icons); i++) {
      const x = box.x + size * (1.8 + i * 1.05);
      ctx.save();
      if (icons - i < 1) { ctx.beginPath(); ctx.rect(x - size / 2, y - size / 2, size / 2, size); ctx.clip(); }
      drawEmoji(ctx, FACE, x, y, size * 0.9);
      ctx.restore();
    }
  });
  if (legend) drawText(ctx, `${FACE} = ${KEY} niños`, { x: box.x, y: box.y + rh * rows.length, w: box.w, h: rh * 0.8 }, '#4E342E');
}

/** Bars on a 0..TOP scale: a line for every vote and a number every 5. */
function barChart(ctx, box, data) {
  const left = box.x + box.w * 0.12;
  const bottom = box.y + box.h * 0.82;
  const unit = (box.h * 0.76) / TOP;
  const colW = (box.x + box.w - left) / data.length;
  ctx.save();
  ctx.fillStyle = '#37474F';
  ctx.font = `bold ${Math.round(box.h * 0.06)}px Nunito, sans-serif`;
  ctx.textAlign = 'right';
  ctx.textBaseline = 'middle';
  for (let v = 0; v <= TOP; v++) {
    ctx.strokeStyle = v % 5 ? 'rgba(0,0,0,0.07)' : 'rgba(0,0,0,0.25)';
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(left, bottom - v * unit); ctx.lineTo(box.x + box.w, bottom - v * unit); ctx.stroke();
    if (v % 5 === 0) ctx.fillText(String(v), left - 4, bottom - v * unit);
  }
  data.forEach(([art, n, color], i) => {
    const x = left + colW * (i + 0.2);
    ctx.fillStyle = color;
    ctx.fillRect(x, bottom - n * unit, colW * 0.6, n * unit);
    drawEmoji(ctx, art, x + colW * 0.3, bottom + box.h * 0.09, Math.min(colW * 0.5, box.h * 0.15));
  });
  ctx.restore();
}

const faces = (data) => data.map(([art, n]) => [art, n / KEY]);
const count = (art) => FAVORITES.find(([a]) => a === art)[1];

function tool(icon, word) {
  return (ctx, box) => {
    drawEmoji(ctx, icon, box.x + box.w / 2, box.y + box.h * 0.4, Math.min(box.w, box.h) * 0.5);
    drawText(ctx, word, { x: box.x, y: box.y + box.h * 0.72, w: box.w, h: box.h * 0.22 });
  };
}

export default class PictogramasLesson extends ChoiceLesson {
  get intro() { return '¡Preguntamos a los niños de tercero qué fruta les gusta más!'; }
  get colors() { return ['#EFEBE9', '#F1F8E9']; }

  makeRounds() {
    const scene = (ctx, box) => pictogram(ctx, box, faces(FAVORITES));
    const hens = VOTES[0][1];
    const farm = [[gallina, 6], [vaca, 4]];
    const swapped = [[gallina, farm[1][1] / KEY], [vaca, farm[0][1] / KEY]];
    return [
      {
        say: `En este pictograma cada carita vale ${KEY} niños. ¿Cuántos niños eligieron el mango?`,
        ask: '¿Cuántos niños eligieron mango?',
        hint: `Cuenta las caritas del mango y suma ${KEY} por cada una.`,
        scene,
        choices: pickChoices(count(mango), [count(mango) / KEY, count(mango) + KEY]),
      },
      {
        say: `¿Cuántos niños eligieron el banano? Media carita vale ${KEY / 2} niño.`,
        ask: '¿Cuántos niños eligieron banano?',
        hint: `Cada carita completa vale ${KEY}, y la media carita vale ${KEY / 2}.`,
        scene,
        choices: pickChoices(count(banano), [Math.ceil(count(banano) / KEY), count(banano) + 1]),
      },
      {
        say: 'En la granja votaron por su animal favorito. Mira la gráfica de barras. ¿Cuántos votos tiene la gallina?',
        ask: '¿Cuántos votos tiene la gallina?',
        hint: 'Busca el número 10 y sigue contando las rayitas hasta arriba de la barra.',
        scene: (ctx, box) => barChart(ctx, box, VOTES),
        choices: pickChoices(hens, [hens - (hens % 5), hens + 1]),
      },
      {
        say: '¿Qué harías para saber qué fruta les gusta a tus compañeros?',
        ask: '¿Cómo recoges la información?',
        hint: 'Para saber lo que piensan, hay que preguntarle a cada uno.',
        choices: [['📋', 'encuesta'], ['🔮', 'adivinar'], ['📺', 'televisión']]
          .map(([icon, word]) => ({ value: word, correct: word === 'encuesta', draw: tool(icon, word) })),
      },
      {
        say: `Contamos ${farm[0][1]} gallinas y ${farm[1][1]} vacas. Si cada carita vale ${KEY}, ¿qué pictograma lo muestra?`,
        ask: `¿Cuál muestra ${farm[0][1]} gallinas y ${farm[1][1]} vacas?`,
        hint: `Cada carita vale ${KEY}: divide cada cantidad entre ${KEY}.`,
        choices: stacked([farm, faces(farm), swapped].map((rows, i) => ({
          value: rows.map(([, n]) => n).join('-') + (i === 0 ? ' sin clave' : ''),
          correct: rows.every(([a, n], r) => a === farm[r][0] && n === farm[r][1] / KEY),
          draw: (ctx, box) => pictogram(ctx, box, rows, { legend: false }),
        }))),
      },
    ];
  }
}
