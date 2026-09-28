// Nivel 6 · Ángulos Agudo, Recto y Obtuso
// CNB Tercero, competencia 6 — 6.1.2 (clasificación de ángulos recto, agudo y obtuso), 6.1.1
// (identificación de ángulos) y 6.1.3 (triángulo rectángulo al partir un rectángulo por la
// diagonal). El tipo de ángulo sale de sus grados; el ángulo recto de un triángulo, de sus lados.
import { ChoiceLesson, numberChoices, pickChoices, stacked } from '../shared/choice-lesson.js';
import { center } from '../shared/draw.js';

const TYPES = ['agudo', 'recto', 'obtuso'];
const typeOf = (deg) => (deg < 90 ? 'agudo' : deg === 90 ? 'recto' : 'obtuso');

function angle(deg) {
  return (ctx, box) => {
    const { cx, cy } = center(box);
    const len = Math.min(box.w, box.h) * 0.6;
    const [vx, vy] = [cx - len * 0.3, cy + len * 0.3];
    const a = (deg * Math.PI) / 180;
    ctx.save();
    ctx.strokeStyle = '#5D4037';
    ctx.lineWidth = 6;
    ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(vx + len * 0.8, vy); ctx.lineTo(vx, vy); ctx.lineTo(vx + Math.cos(a) * len * 0.8, vy - Math.sin(a) * len * 0.8); ctx.stroke();
    ctx.strokeStyle = '#EF6C00';
    ctx.lineWidth = 3;
    ctx.beginPath(); ctx.arc(vx, vy, len * 0.18, -a, 0); ctx.stroke();
    ctx.restore();
  };
}

// Corners in grid units (y grows down); a corner is right when its two sides are perpendicular.
const rightCorners = (pts) => pts.filter((p, i) => {
  const [a, b] = [pts[(i + pts.length - 1) % pts.length], pts[(i + 1) % pts.length]];
  return (a[0] - p[0]) * (b[0] - p[0]) + (a[1] - p[1]) * (b[1] - p[1]) === 0;
}).length;

function polygon(pts, { dashed = null } = {}) {
  return (ctx, box) => {
    const xs = pts.map((p) => p[0]);
    const ys = pts.map((p) => p[1]);
    const [w, h] = [Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)];
    const s = Math.min((box.w * 0.8) / w, (box.h * 0.8) / h);
    const P = ([x, y]) => [box.x + (box.w - w * s) / 2 + (x - Math.min(...xs)) * s, box.y + (box.h - h * s) / 2 + (y - Math.min(...ys)) * s];
    ctx.save();
    ctx.fillStyle = '#EF9A9A';
    ctx.strokeStyle = '#C62828';
    ctx.lineWidth = 3;
    ctx.beginPath(); pts.forEach((p) => ctx.lineTo(...P(p))); ctx.closePath(); ctx.fill(); ctx.stroke();
    if (dashed) {
      ctx.setLineDash([8, 6]);
      ctx.strokeStyle = '#1565C0';
      ctx.beginPath(); ctx.moveTo(...P(dashed[0])); ctx.lineTo(...P(dashed[1])); ctx.stroke();
    }
    ctx.restore();
  };
}

function kind(deg, say) {
  return {
    say,
    ask: '¿Qué tipo de ángulo es?',
    hint: 'Compáralo con la esquina de tu cuaderno: más cerrado es agudo, igual es recto, más abierto es obtuso.',
    scene: angle(deg),
    choices: pickChoices(typeOf(deg), TYPES),
  };
}

function find(type, degrees, say) {
  return {
    say,
    ask: `¿Cuál es un ángulo ${type}?`,
    hint: 'La esquina del cuaderno es un ángulo recto. Compara cada ángulo con ella.',
    choices: stacked(degrees.map((deg) => ({ correct: typeOf(deg) === type, draw: angle(deg) }))),
  };
}

export default class AngulosLesson extends ChoiceLesson {
  get intro() { return '¡Hay ángulos cerrados, rectos y abiertos!'; }
  get colors() { return ['#FFEBEE', '#FFF8E1']; }

  makeRounds() {
    const rect = [[0, 0], [4, 0], [4, 3], [0, 3]];
    const halves = [[[0, 0], [4, 0], [4, 3]], [[0, 3], [2, 0], [4, 3]], [[0, 3], [4, 3], [5, 1]]];
    const half = halves[0];
    return [
      find('agudo', [90, 40, 130], '¿Cuál es un ángulo agudo? Es más cerrado que la esquina del cuaderno.'),
      find('obtuso', [140, 60, 90], '¿Cuál es un ángulo obtuso? Es más abierto que la esquina del cuaderno.'),
      kind(120, 'Mira este ángulo. ¿Es agudo, recto u obtuso?'),
      kind(35, '¿Y este ángulo? ¿Es agudo, recto u obtuso?'),
      {
        say: 'Cortamos este rectángulo por la línea azul, la diagonal. ¿Qué triángulo sale?',
        ask: '¿Qué triángulo sale al cortar?',
        hint: 'Al cortar, cada triángulo se queda con una esquina del rectángulo, que es recta.',
        scene: polygon(rect, { dashed: [rect[0], rect[2]] }),
        choices: halves.map((pts) => ({ correct: rightCorners(pts) > 0, draw: polygon(pts) })),
      },
      {
        say: 'Este es un triángulo rectángulo. ¿Cuántos ángulos rectos tiene?',
        ask: '¿Cuántos ángulos rectos tiene?',
        hint: 'Busca las esquinas que son como la del cuaderno.',
        scene: polygon(half),
        choices: numberChoices(rightCorners(half), { max: 9 }),
      },
    ];
  }
}
