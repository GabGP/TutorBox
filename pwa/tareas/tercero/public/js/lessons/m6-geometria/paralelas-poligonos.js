// Nivel 6 · Líneas Paralelas y Polígonos
// CNB Tercero, competencia 6 — 6.1.4 (líneas paralelas en objetos de su entorno) y 6.1.5 (figuras
// de 3 y 4 lados en un arreglo de puntos, con regla). Paralelas y lados se calculan con los puntos.
import { ChoiceLesson, numberChoices, stacked } from '../shared/choice-lesson.js';

const COLS = 6;
const ROWS = 5;
const dir = ([a, b]) => [b[0] - a[0], b[1] - a[1]];
const parallel = (s, t) => { const [u, v] = [dir(s), dir(t)]; return u[0] * v[1] - u[1] * v[0] === 0; };
const edges = (pts) => pts.map((p, i) => [p, pts[(i + 1) % pts.length]]);
const parallelPairs = (pts) => {
  const e = edges(pts);
  return e.reduce((n, s, i) => n + e.slice(i + 1).filter((t) => parallel(s, t)).length, 0);
};

/** A board of dots (0..COLS-1 by 0..ROWS-1); returns grid point -> canvas point. */
function dots(ctx, box) {
  const c = Math.min(box.w / COLS, box.h / ROWS);
  const x0 = box.x + (box.w - c * (COLS - 1)) / 2;
  const y0 = box.y + (box.h - c * (ROWS - 1)) / 2;
  ctx.fillStyle = '#90A4AE';
  for (let i = 0; i < COLS; i++) for (let j = 0; j < ROWS; j++) { ctx.beginPath(); ctx.arc(x0 + i * c, y0 + j * c, 3, 0, Math.PI * 2); ctx.fill(); }
  return ([x, y]) => [x0 + x * c, y0 + y * c];
}

function figure(pts) {
  return (ctx, box) => {
    const P = dots(ctx, box);
    ctx.save();
    ctx.fillStyle = 'rgba(239,154,154,0.6)';
    ctx.strokeStyle = '#C62828';
    ctx.lineWidth = 3;
    ctx.beginPath(); pts.forEach((p) => ctx.lineTo(...P(p))); ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.restore();
  };
}

function segments(pair) {
  return (ctx, box) => {
    const P = dots(ctx, box);
    ctx.save();
    ctx.strokeStyle = '#1565C0';
    ctx.lineWidth = 5;
    ctx.lineCap = 'round';
    pair.forEach(([a, b]) => { ctx.beginPath(); ctx.moveTo(...P(a)); ctx.lineTo(...P(b)); ctx.stroke(); });
    ctx.restore();
  };
}

export default class ParalelasPoligonosLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a trazar líneas y figuras con regla!'; }
  get colors() { return ['#FFEBEE', '#E3F2FD']; }

  makeRounds() {
    // Stacked cards are not shuffled: this order is the order on screen.
    const pairs = [
      [[[0, 0], [4, 4]], [[0, 4], [4, 0]]],
      [[[0, 0], [2, 4]], [[2, 0], [4, 4]]],
      [[[0, 4], [2, 0]], [[4, 4], [2, 0]]],
    ];
    const quad = [[1, 1], [4, 0], [5, 3], [2, 4]];
    const tri = [[1, 4], [3, 1], [5, 4]];
    const shapes = [[[1, 1], [5, 1], [4, 4], [2, 4]], [[1, 2], [3, 0], [5, 2], [3, 4]], tri];
    const rect = [[1, 1], [5, 1], [5, 3], [1, 3]];
    return [
      {
        say: '¿Qué par de líneas es paralelo? Las paralelas nunca se juntan, como los rieles del tren.',
        ask: '¿Cuáles líneas son paralelas?',
        hint: 'Imagina que las líneas siguen y siguen. Las paralelas nunca se tocan.',
        choices: stacked(pairs.map((p) => ({ correct: parallel(p[0], p[1]), draw: segments(p) }))),
      },
      {
        say: 'Unimos estos puntos con una regla. ¿Cuántos lados tiene la figura?',
        ask: '¿Cuántos lados tiene la figura?',
        hint: 'Pasa el dedo por cada lado, de punto a punto, y cuéntalos.',
        scene: figure(quad),
        choices: numberChoices(quad.length, { min: 3, max: 9 }),
      },
      {
        say: '¿Cuál de estas figuras es un triángulo?',
        ask: '¿Cuál es un triángulo?',
        hint: 'El triángulo tiene 3 lados y 3 puntas.',
        choices: stacked(shapes.map((pts) => ({ correct: pts.length === 3, draw: figure(pts) }))),
      },
      {
        say: 'En el rectángulo, los lados de enfrente son paralelos. ¿Cuántos pares de lados paralelos tiene?',
        ask: '¿Cuántos pares de lados paralelos?',
        hint: 'El lado de arriba con el de abajo es un par. Busca otro.',
        scene: figure(rect),
        choices: numberChoices(parallelPairs(rect), { max: 9 }),
      },
      {
        say: '¿Y este triángulo, cuántos pares de lados paralelos tiene?',
        ask: '¿Cuántos pares paralelos tiene?',
        hint: 'Si alargas los lados del triángulo, todos se cruzan.',
        scene: figure(tri),
        choices: numberChoices(parallelPairs(tri), { max: 9 }),
      },
    ];
  }
}
