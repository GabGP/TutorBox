// Nivel 2 · Dibujos con Pares Ordenados
// CNB Tercero, competencia 2 — 2.2.2 (elaboración de dibujos siguiendo pares ordenados en el
// primer cuadrante). La figura se reconoce en código a partir de los puntos; el distractor
// principal es el mismo dibujo con cada par al revés.
import { ChoiceLesson, pickChoices, stacked } from '../shared/choice-lesson.js';
import { drawShape, drawText } from '../shared/draw.js';
import { grid } from './plano-cardinal.js';

const pair = ([x, y]) => `(${x}, ${y})`;
const swap = (pts) => pts.map(([x, y]) => [y, x]);
const LETTERS = 'ABCD';
const SHAPE = { triángulo: 'triangle', cuadrado: 'square', rectángulo: 'rectangle' };

/** Which figure the points make when joined in order. */
function figureOf(pts) {
  if (pts.length === 3) return 'triángulo';
  const sides = pts.map((p, i) => {
    const q = pts[(i + 1) % pts.length];
    return Math.hypot(q[0] - p[0], q[1] - p[1]);
  });
  return sides.every((s) => s === sides[0]) ? 'cuadrado' : 'rectángulo';
}

function plot(ctx, box, pts, { join = false, open = false, labels = true } = {}) {
  const { at, cell } = grid(ctx, box, { labels });
  const P = (p) => at(p[0], p[1]);
  if (join || open) {
    ctx.save();
    ctx.strokeStyle = '#C62828';
    ctx.fillStyle = 'rgba(239,154,154,0.5)';
    ctx.lineWidth = 3;
    if (open) ctx.setLineDash([7, 5]);
    ctx.beginPath();
    pts.forEach((p) => ctx.lineTo(P(p).x, P(p).y));
    if (join) { ctx.closePath(); ctx.fill(); }
    ctx.stroke();
    ctx.restore();
  }
  pts.forEach((p, i) => {
    ctx.fillStyle = '#1565C0';
    ctx.beginPath(); ctx.arc(P(p).x, P(p).y, Math.max(4, cell * 0.12), 0, Math.PI * 2); ctx.fill();
    if (labels) drawText(ctx, LETTERS[i], { x: P(p).x + 2, y: P(p).y - cell * 0.7, w: cell * 0.6, h: cell * 0.5 }, '#1565C0');
  });
}

function whichFigure(pts) {
  const answer = figureOf(pts);
  const names = pts.map((p, i) => `${LETTERS[i]} ${pair(p)}`).join(', ');
  return {
    say: `Une los puntos en orden: ${names}, y vuelve al primero. ¿Qué figura se forma?`,
    ask: '¿Qué figura forman los puntos?',
    hint: 'Imagina las líneas de un punto al siguiente. Cuenta los lados y mira si son iguales.',
    scene: (ctx, box) => plot(ctx, box, pts),
    choices: Object.keys(SHAPE).map((name) => ({
      value: name,
      correct: name === answer,
      draw: (ctx, box) => drawShape(ctx, SHAPE[name], box.x + box.w / 2, box.y + box.h / 2, Math.min(box.w, box.h) * 0.3, '#EF9A9A'),
    })),
  };
}

export default class DibujoParesLesson extends ChoiceLesson {
  get intro() { return '¡Con pares ordenados podemos dibujar!'; }
  get colors() { return ['#E8F5E9', '#FFF8E1']; }

  makeRounds() {
    const tri = [[1, 1], [3, 4], [5, 1]];
    const almost = [[1, 1], [3, 3], [5, 1]];
    const corner = [[1, 1], [4, 1], [4, 3]];
    const missing = [corner[0][0], corner[2][1]];
    return [
      whichFigure([[1, 1], [5, 1], [5, 3], [1, 3]]),
      whichFigure([[1, 1], [4, 1], [4, 4], [1, 4]]),
      {
        say: `¿Qué dibujo muestra los puntos ${tri.map(pair).join(', ')} unidos?`,
        ask: `¿Cuál une ${tri.map(pair).join(' ')}?`,
        hint: 'El primer número de cada par va hacia la derecha y el segundo hacia arriba.',
        choices: stacked([swap(tri), tri, almost].map((pts) => ({
          value: pts.map(pair).join(' '),
          correct: pts.map(pair).join(' ') === tri.map(pair).join(' '),
          draw: (ctx, box) => plot(ctx, box, pts, { join: true, labels: false }),
        }))),
      },
      {
        say: `Para terminar el rectángulo falta un punto. Ya están ${corner.map(pair).join(', ')}. ¿Qué punto falta?`,
        ask: '¿Qué punto falta para el rectángulo?',
        hint: 'El punto que falta está arriba del primero y a la misma altura que el último.',
        scene: (ctx, box) => plot(ctx, box, corner, { open: true }),
        choices: pickChoices(pair(missing), [pair([missing[1], missing[0]]), pair([missing[0], missing[1] + 1])]),
      },
    ];
  }
}
