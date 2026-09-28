// Nivel 2 · Caminos con Puntos Cardinales
// CNB Tercero, competencia 2 — 2.2.1 (desplazamientos en el primer cuadrante del plano cartesiano
// con instrucciones que usan los puntos cardinales) y 2.1.2 (desplazamientos con un punto de
// referencia). Distractor principal: hacer los dos movimientos al revés.
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { drawEmoji, drawQuq, drawText } from '../shared/draw.js';
import { cerdo, elote, gallina, mango, pollito, tomate } from '../shared/art.js';

export const MAX = 5;

/** The first quadrant from 0 to MAX; returns (gx, gy) -> canvas point and the cell size. */
export function grid(ctx, box, { labels = true } = {}) {
  const pad = labels ? Math.min(box.w, box.h) * 0.1 : 6;
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
  if (labels) {
    ctx.fillStyle = '#37474F';
    ctx.font = `bold ${Math.round(cell * 0.38)}px Nunito, sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    for (let i = 0; i <= MAX; i++) {
      ctx.fillText(String(i), at(i, 0).x, y0 + cell * 0.35);
      if (i) ctx.fillText(String(i), x0 - cell * 0.35, at(0, i).y);
    }
  }
  ctx.restore();
  return { at, cell };
}

const THINGS = [
  { art: elote, name: 'el elote', x: 3, y: 2 },
  { art: mango, name: 'el mango', x: 2, y: 3 },
  { art: pollito, name: 'el pollito', x: 2, y: 1 },
  { art: gallina, name: 'la gallina', x: 1, y: 4 },
  { art: cerdo, name: 'el cerdo', x: 4, y: 1 },
  { art: tomate, name: 'el tomate', x: 4, y: 3 },
];
// On the plane the Norte is up (y grows) and the Este is to the right (x grows).
const MOVES = { Este: [1, 0], Oeste: [-1, 0], Norte: [0, 1], Sur: [0, -1] };
const WAY = { Este: 'a la derecha', Oeste: 'a la izquierda', Norte: 'hacia arriba', Sur: 'hacia abajo' };

const go = (p, dir, n) => ({ x: p.x + MOVES[dir][0] * n, y: p.y + MOVES[dir][1] * n });
const thingAt = (p) => THINGS.find((t) => t.x === p.x && t.y === p.y);

function scene(from) {
  return (ctx, box) => {
    const { at, cell } = grid(ctx, box);
    THINGS.forEach(({ art, x, y }) => drawEmoji(ctx, art, at(x, y).x, at(x, y).y, cell * 0.85));
    drawQuq(ctx, at(from.x, from.y).x, at(from.x, from.y).y - cell * 0.1, cell * 1.1);
    // The compass sits right of the grid, where no point is used.
    const side = at(MAX, MAX / 2);
    drawText(ctx, 'N', { x: side.x + cell * 0.1, y: side.y - cell * 0.8, w: cell * 0.6, h: cell * 0.5 }, '#1565C0');
    drawText(ctx, '↑', { x: side.x + cell * 0.1, y: side.y - cell * 0.35, w: cell * 0.6, h: cell * 0.6 }, '#1565C0');
  };
}

function walk(from, [d1, a], [d2, b]) {
  const answer = thingAt(go(go(from, d1, a), d2, b));
  const others = [thingAt(go(go(from, d1, b), d2, a)), ...THINGS]
    .filter((t, i, all) => t && t !== answer && all.indexOf(t) === i).slice(0, 2);
  return {
    say: `Q'uq' camina ${a} cuadros al ${d1} y luego ${b} al ${d2}. ¿Qué encuentra?`,
    ask: `${a} al ${d1}, ${b} al ${d2}`,
    hint: `El ${d1} es ${WAY[d1]} y el ${d2} es ${WAY[d2]}. Primero ${a} cuadros al ${d1}.`,
    scene: scene(from),
    choices: [answer, ...others].map((t) => ({
      correct: t === answer,
      draw: (ctx, box) => drawEmoji(ctx, t.art, box.x + box.w / 2, box.y + box.h / 2, Math.min(box.w, box.h) * 0.8),
    })),
  };
}

const steps = ([d1, a], [d2, b]) => `${a} ${d1}, ${b} ${d2}`;

export default class PlanoCardinalLesson extends ChoiceLesson {
  get intro() { return '¡Ayuda a Q\'uq\' a caminar con los puntos cardinales!'; }
  get colors() { return ['#E8F5E9', '#E1F5FE']; }

  makeRounds() {
    const origin = { x: 0, y: 0 };
    const target = THINGS.find((t) => t.name === 'el tomate');
    return [
      walk(origin, ['Este', 3], ['Norte', 2]),
      walk({ x: 0, y: 4 }, ['Este', 2], ['Sur', 3]),
      walk({ x: 5, y: 5 }, ['Oeste', 4], ['Sur', 1]),
      {
        say: `Q'uq' está en el 0, 0 y quiere llegar al tomate. ¿Qué instrucción debe seguir?`,
        ask: '¿Cómo llega al tomate?',
        hint: 'Cuenta cuántos cuadros al Este está el tomate, y cuántos al Norte.',
        scene: scene(origin),
        choices: pickChoices(steps(['Este', target.x], ['Norte', target.y]),
          [steps(['Este', target.y], ['Norte', target.x]), steps(['Oeste', target.x], ['Sur', target.y])]),
      },
    ];
  }
}
