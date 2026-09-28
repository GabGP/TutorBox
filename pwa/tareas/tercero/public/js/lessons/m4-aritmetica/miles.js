// Nivel 4 · Hasta 10,000
// CNB Tercero, competencia 4 — 4.1.6 (valor relativo de un dígito de 0 a 10,000), 4.1.2 (lectura y
// escritura de números hasta 10,000) y 4.1.5 (unidades, decenas, centenas y unidades de millar).
// Distractores: saltarse el lugar vacío (3,407 -> 347) y el valor del dígito sin su lugar.
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { center, drawText, num } from '../shared/draw.js';

const PLACES = [['UM', '#8E24AA'], ['C', '#FB8C00'], ['D', '#1E88E5'], ['U', '#43A047']];
const digitsOf = (n) => String(n).padStart(4, '0').split('').map(Number);
const fromDigits = (d) => d.reduce((a, x) => a * 10 + x, 0);

/** A place-value chart with one counter per unit in each column. */
function chart(ctx, box, d) {
  const w = box.w / PLACES.length;
  PLACES.forEach(([label, color], i) => {
    const x = box.x + w * i;
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.strokeRect(x + 3, box.y + 2, w - 6, box.h - 4);
    drawText(ctx, label, { x, y: box.y + 4, w, h: box.h * 0.16 }, color);
    const r = Math.min(w / 8, box.h / 14);
    for (let k = 0; k < d[i]; k++) {
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(x + w / 2 + ((k % 3) - 1) * r * 2.5, box.y + box.h * 0.32 + Math.floor(k / 3) * r * 2.5, r, 0, Math.PI * 2);
      ctx.fill();
    }
  });
}

/** The number written big, with the digit at `index` (0 = thousands) painted orange. */
function highlighted(ctx, box, n, index) {
  const text = num(n);
  const size = Math.min(box.h * 0.4, (box.w * 0.8) / (text.length * 0.6));
  ctx.save();
  ctx.font = `900 ${Math.round(size)}px Nunito, sans-serif`;
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  let x = box.x + (box.w - ctx.measureText(text).width) / 2;
  let digit = -1;
  [...text].forEach((ch) => {
    if (ch !== ',') digit++;
    ctx.fillStyle = ch !== ',' && digit === index ? '#EF6C00' : '#1F2A1F';
    ctx.fillText(ch, x, box.y + box.h / 2);
    x += ctx.measureText(ch).width;
  });
  ctx.restore();
}

function readChart(n) {
  const d = digitsOf(n);
  const skipZero = Number(d.filter((x) => x).join(''));
  return {
    say: 'La tabla tiene fichas en cada lugar: unidades de millar, centenas, decenas y unidades. ¿Qué número forman?',
    ask: '¿Qué número forman las fichas?',
    hint: `Hay ${d[0]} unidades de millar, ${d[1]} centenas, ${d[2]} decenas y ${d[3]} unidades. Donde no hay fichas va un cero.`,
    scene: (ctx, box) => chart(ctx, box, d),
    choices: pickChoices(n, [skipZero, fromDigits([d[0], d[1], d[3], d[2]])]),
  };
}

export default class MilesLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a leer números de miles!'; }
  get colors() { return ['#FFFDE7', '#E3F2FD']; }

  makeRounds() {
    const [n, at] = [6582, 1];
    const value = digitsOf(n)[at] * 10 ** (3 - at);
    const m = 4265;
    const md = digitsOf(m);
    const last = 9999;
    return [
      readChart(3407),
      {
        say: `En el número ${num(n)}, ¿cuánto vale el 5?`,
        ask: `En ${num(n)}, ¿cuánto vale el 5?`,
        hint: 'El 5 está en el lugar de las centenas. Cinco centenas valen...',
        scene: (ctx, box) => highlighted(ctx, box, n, at),
        choices: pickChoices(value, [value / 100, value * 10]),
      },
      readChart(1050),
      {
        say: `En el número ${num(m)}, ¿qué dígito está en el lugar de las centenas?`,
        ask: '¿Qué cifra está en las centenas?',
        hint: 'Desde la derecha: unidades, decenas, centenas.',
        scene: (ctx, box) => highlighted(ctx, box, m, -1),
        choices: pickChoices(md[1], [md[0], md[2]]),
      },
      {
        say: '¿Cuál es el número cuatro mil noventa?',
        ask: '¿Cuál es cuatro mil noventa?',
        hint: 'Cuatro mil son 4 unidades de millar. No hay centenas, y noventa son 9 decenas.',
        choices: pickChoices(4 * 1000 + 90, [4900, 490]),
      },
      {
        say: `¿Qué número viene justo después de ${num(last)}?`,
        ask: `¿Qué sigue después de ${num(last)}?`,
        hint: 'Suma 1: todas las cifras se llenan y pasamos a diez mil.',
        scene: (ctx, box) => { const { cx } = center(box); drawText(ctx, `${num(last)} → ?`, { x: cx - box.w * 0.4, y: box.y + box.h * 0.3, w: box.w * 0.8, h: box.h * 0.4 }); },
        choices: pickChoices(last + 1, [last - 1, 1000]),
      },
    ];
  }
}
