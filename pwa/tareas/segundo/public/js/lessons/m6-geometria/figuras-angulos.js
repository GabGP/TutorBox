// Nivel 6 · Lados, Vértices y Ángulos Rectos
// CNB Segundo, competencia 6 — 6.1.3 (triángulos y cuadriláteros por su número de lados y
// vértices), 6.1.1 y 6.1.2 (el ángulo recto en el entorno, el cuadrado y el rectángulo), 6.1.4
// (semejanzas y diferencias) y 6.3.1 (segmentos horizontales y verticales).
import { ChoiceLesson, numberChoices } from '../shared/choice-lesson.js';
import { center, drawShape } from '../shared/draw.js';

// Corners of each figure exactly as drawShape draws it, as multiples of its half-size r.
const CORNERS = {
  triangle: [[0, -1], [1.05, 0.8], [-1.05, 0.8]],
  square: [[-0.85, -0.85], [0.85, -0.85], [0.85, 0.85], [-0.85, 0.85]],
  rectangle: [[-1.2, -0.65], [1.2, -0.65], [1.2, 0.65], [-1.2, 0.65]],
};
const RIGHT_ANGLES = { triangle: 0, square: 4, rectangle: 4 };
const EQUAL_SIDES = { square: true, rectangle: false };

function figure(kind, { dots = false } = {}) {
  return (ctx, box) => {
    const { cx, cy } = center(box);
    const r = Math.min(box.w / 2.6, box.h / 2.2) * 0.9;
    drawShape(ctx, kind, cx, cy, r, '#EF9A9A');
    if (!dots) return;
    ctx.fillStyle = '#C62828';
    CORNERS[kind].forEach(([x, y]) => { ctx.beginPath(); ctx.arc(cx + x * r, cy + y * r, 7, 0, Math.PI * 2); ctx.fill(); });
  };
}

function angle(deg) {
  return (ctx, box) => {
    const { cx, cy } = center(box);
    const len = Math.min(box.w, box.h) * 0.6;
    const [vx, vy] = [cx - len * 0.35, cy + len * 0.3];
    const a = (deg * Math.PI) / 180;
    ctx.save();
    ctx.strokeStyle = '#5D4037';
    ctx.lineWidth = 6;
    ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(vx + len * 0.8, vy); ctx.lineTo(vx, vy); ctx.lineTo(vx + Math.cos(a) * len * 0.8, vy - Math.sin(a) * len * 0.8); ctx.stroke();
    ctx.restore();
  };
}

function segment([dx, dy]) {
  return (ctx, box) => {
    const { cx, cy } = center(box);
    const len = Math.min(box.w, box.h) * 0.35;
    ctx.save();
    ctx.strokeStyle = '#1565C0';
    ctx.lineWidth = 7;
    ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(cx - dx * len, cy - dy * len); ctx.lineTo(cx + dx * len, cy + dy * len); ctx.stroke();
    ctx.restore();
  };
}

export default class FigurasAngulosLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a descubrir los secretos de las figuras de la Antigua!'; }
  get colors() { return ['#FFEBEE', '#FFF8E1']; }

  makeRounds() {
    const LINES = { vertical: [0, 1], horizontal: [1, 0], inclinada: [0.7, 0.7] };
    return [
      {
        say: '¿Cuál tiene una esquina como la de tu cuaderno? Esa esquina se llama ángulo recto.',
        ask: '¿Cuál es un ángulo recto?',
        hint: 'Pon la esquina de tu cuaderno encima. El ángulo recto encaja justo.',
        choices: [90, 45, 135].map((deg) => ({ correct: deg === 90, draw: angle(deg) })),
      },
      {
        say: '¿Cuántos lados tiene el triángulo?',
        ask: '¿Cuántos lados tiene el triángulo?',
        hint: 'Pasa tu dedo por cada lado y cuéntalos.',
        scene: figure('triangle'),
        choices: numberChoices(CORNERS.triangle.length, { max: 9 }),
      },
      {
        say: 'Los vértices son las esquinas. ¿Cuántos vértices tiene el rectángulo?',
        ask: '¿Cuántos vértices tiene el rectángulo?',
        hint: 'Cuenta los puntos rojos de las esquinas.',
        scene: figure('rectangle', { dots: true }),
        choices: numberChoices(CORNERS.rectangle.length, { max: 9 }),
      },
      {
        say: '¿Cuántos ángulos rectos tiene el cuadrado?',
        ask: '¿Cuántos ángulos rectos tiene el cuadrado?',
        hint: 'Todas las esquinas del cuadrado son como la esquina del cuaderno.',
        scene: figure('square'),
        choices: numberChoices(RIGHT_ANGLES.square, { max: 9 }),
      },
      {
        say: 'El cuadrado y el rectángulo tienen 4 lados. ¿Cuál tiene TODOS sus lados del mismo tamaño?',
        ask: '¿Cuál tiene los 4 lados iguales?',
        hint: 'El rectángulo tiene dos lados largos y dos cortos.',
        choices: ['square', 'rectangle'].map((kind) => ({ correct: EQUAL_SIDES[kind], draw: figure(kind) })),
      },
      {
        say: '¿Cuál línea es VERTICAL, parada como un poste?',
        ask: '¿Cuál línea es vertical?',
        hint: 'Vertical es de arriba hacia abajo, como un poste o un árbol.',
        choices: Object.entries(LINES).map(([name, dir]) => ({ correct: name === 'vertical', draw: segment(dir) })),
      },
    ];
  }
}
