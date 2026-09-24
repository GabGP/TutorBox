// Nivel 2 · Puntos en el Plano
// CNB Segundo, competencia 2 — 2.2.2 (ubicación de puntos en el primer cuadrante del plano
// cartesiano dado pares ordenados). Los distractores cambian el orden del par: (3, 2) contra (2, 3).
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { drawEmoji } from '../shared/draw.js';
import { elote, gallina, mango, vaca } from '../shared/art.js';

export const MAX = 5;

/** Draws the first quadrant from 0 to MAX and returns (gx, gy) -> canvas point, plus the cell size. */
export function grid(ctx, box) {
  const pad = Math.min(box.w, box.h) * 0.1;
  const cell = Math.min((box.w - pad * 1.6) / MAX, (box.h - pad * 1.6) / MAX);
  const x0 = box.x + (box.w - cell * MAX) / 2 + pad * 0.3;
  const y0 = box.y + box.h - (box.h - cell * MAX) / 2 + pad * 0.3;
  const at = (gx, gy) => ({ x: x0 + gx * cell, y: y0 - gy * cell });
  ctx.save();
  ctx.strokeStyle = 'rgba(0,0,0,0.15)';
  ctx.lineWidth = 1;
  for (let i = 0; i <= MAX; i++) {
    ctx.beginPath(); ctx.moveTo(at(i, 0).x, at(i, 0).y); ctx.lineTo(at(i, MAX).x, at(i, MAX).y); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(at(0, i).x, at(0, i).y); ctx.lineTo(at(MAX, i).x, at(MAX, i).y); ctx.stroke();
  }
  ctx.strokeStyle = '#37474F';
  ctx.lineWidth = 3;
  ctx.beginPath(); ctx.moveTo(at(0, MAX).x, at(0, MAX).y); ctx.lineTo(x0, y0); ctx.lineTo(at(MAX, 0).x, at(MAX, 0).y); ctx.stroke();
  ctx.fillStyle = '#37474F';
  ctx.font = `bold ${Math.round(cell * 0.38)}px Nunito, sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  for (let i = 0; i <= MAX; i++) {
    ctx.fillText(String(i), at(i, 0).x, y0 + cell * 0.35);
    if (i) ctx.fillText(String(i), x0 - cell * 0.35, at(0, i).y);
  }
  ctx.restore();
  return { at, cell };
}

export function drawThings(ctx, box, things) {
  const { at, cell } = grid(ctx, box);
  things.forEach(({ art, x, y }) => drawEmoji(ctx, art, at(x, y).x, at(x, y).y, cell * 0.85));
  return { at, cell };
}

const THINGS = [
  { art: mango, name: 'el mango', x: 3, y: 2 },
  { art: vaca, name: 'la vaca', x: 2, y: 3 },
  { art: elote, name: 'el elote', x: 1, y: 4 },
  { art: gallina, name: 'la gallina', x: 4, y: 1 },
];

const pair = (x, y) => `(${x}, ${y})`;
const thingAt = (x, y) => THINGS.find((t) => t.x === x && t.y === y);
const scene = (ctx, box) => drawThings(ctx, box, THINGS);

// "What is at (x, y)?": the wrong answers are the thing at (y, x) and one more.
function whatIsAt(x, y) {
  const answer = thingAt(x, y);
  const others = [thingAt(y, x), ...THINGS].filter((t, i, all) => t && t !== answer && all.indexOf(t) === i).slice(0, 2);
  return {
    say: `¿Qué hay en el punto ${x}, ${y}? Primero camina ${x} hacia la derecha y luego ${y} hacia arriba.`,
    ask: `¿Qué hay en el punto ${pair(x, y)}?`,
    hint: `El primer número, ${x}, es hacia la derecha. El segundo, ${y}, es hacia arriba.`,
    scene,
    choices: [answer, ...others].map((t) => ({
      correct: t === answer,
      draw: (ctx, box) => drawEmoji(ctx, t.art, box.x + box.w / 2, box.y + box.h / 2, Math.min(box.w, box.h) * 0.8),
    })),
  };
}

function whereIs(thing) {
  return {
    say: `¿En qué punto está ${thing.name}?`,
    ask: `¿En qué punto está ${thing.name}?`,
    hint: 'Cuenta primero hacia la derecha por abajo, y después hacia arriba.',
    scene,
    choices: pickChoices(pair(thing.x, thing.y), [pair(thing.y, thing.x), pair(thing.x, thing.y + 1)]),
  };
}

export default class PlanoPuntosLesson extends ChoiceLesson {
  get intro() { return '¡Esta cuadrícula es un mapa! Cada punto tiene dos números.'; }
  get colors() { return ['#E8F5E9', '#E1F5FE']; }

  makeRounds() {
    return [whatIsAt(3, 2), whatIsAt(1, 4), whereIs(THINGS[3]), whereIs(THINGS[1])];
  }
}
