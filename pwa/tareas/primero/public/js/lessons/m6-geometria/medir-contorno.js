// Módulo 6 · Medir el Contorno
// CNB Primero, competencia 6 — 6.2.1 (perímetro de cuadrado y rectángulo con unidades no estándar)
// y 6.1.1 (semejanzas y diferencias entre figuras).
import { ChoiceLesson, numberChoices } from '../shared/choice-lesson.js';
import { drawEmoji, drawShape } from '../shared/draw.js';

// The distance around a cols × rows figure, in units: computed here, never typed by hand.
const perimeter = (cols, rows) => 2 * (cols + rows);

// A garden (or table) of cols × rows units with one stick (or footprint) per unit of border.
function fence(ctx, box, cols, rows, { mark = 'stick', fill = '#AED581' } = {}) {
  const unit = Math.min(box.w / (cols + 1), box.h / (rows + 1));
  const x0 = box.x + (box.w - unit * cols) / 2;
  const y0 = box.y + (box.h - unit * rows) / 2;
  ctx.fillStyle = fill;
  ctx.fillRect(x0, y0, unit * cols, unit * rows);
  const segs = [];
  for (let i = 0; i < cols; i++) {
    segs.push([x0 + i * unit, y0, x0 + (i + 1) * unit, y0]);
    segs.push([x0 + i * unit, y0 + rows * unit, x0 + (i + 1) * unit, y0 + rows * unit]);
  }
  for (let j = 0; j < rows; j++) {
    segs.push([x0, y0 + j * unit, x0, y0 + (j + 1) * unit]);
    segs.push([x0 + cols * unit, y0 + j * unit, x0 + cols * unit, y0 + (j + 1) * unit]);
  }
  const gap = unit * 0.12;
  segs.forEach(([ax, ay, bx, by]) => {
    if (mark === 'step') {
      drawEmoji(ctx, '👣', (ax + bx) / 2, (ay + by) / 2, unit * 0.45);
      return;
    }
    const dx = Math.sign(bx - ax) * gap;
    const dy = Math.sign(by - ay) * gap;
    ctx.strokeStyle = '#8D5524';
    ctx.lineWidth = Math.max(5, unit * 0.12);
    ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(ax + dx, ay + dy); ctx.lineTo(bx - dx, by - dy); ctx.stroke();
  });
}

const shapeCard = (kind, r, correct, hint) => ({
  correct,
  hint,
  draw: (ctx, box) => drawShape(ctx, kind, box.x + box.w / 2, box.y + box.h / 2, Math.min(box.w, box.h) * r, '#43A047'),
});

export default class MedirContornoLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a medir alrededor de las figuras!'; }
  get colors() { return ['#F1F8E9', '#FFF8E1']; }

  makeRounds() {
    return [
      {
        say: 'Don José cercó su huerto cuadrado con palitos. ¿Cuántos palitos hay alrededor del huerto?',
        ask: '¿Cuántos palitos hay alrededor?',
        hint: 'Empieza en una esquina y cuenta cada palito hasta dar toda la vuelta.',
        scene: (ctx, box) => fence(ctx, box, 2, 2),
        choices: numberChoices(perimeter(2, 2), { max: 14 }),
      },
      {
        say: 'Ahora un huerto rectangular. ¿Cuántos palitos hay alrededor?',
        ask: '¿Cuántos palitos hay alrededor?',
        hint: 'Cuenta los palitos de arriba, del lado, de abajo y del otro lado.',
        scene: (ctx, box) => fence(ctx, box, 3, 2),
        choices: numberChoices(perimeter(3, 2), { max: 14 }),
      },
      {
        say: 'Ana camina alrededor de la mesa. Cada huella es un paso. ¿Cuántos pasos da para dar toda la vuelta?',
        ask: '¿Cuántos pasos alrededor de la mesa?',
        hint: 'Cuenta las huellas, una por una, alrededor de la mesa.',
        scene: (ctx, box) => fence(ctx, box, 2, 1, { mark: 'step', fill: '#A1887F' }),
        choices: numberChoices(perimeter(2, 1), { max: 12 }),
      },
      {
        say: '¿Qué figura tiene una FORMA diferente a las demás?',
        ask: '¿Cuál tiene otra forma?',
        hint: 'No importa si es grande o pequeña: mira si es redonda o si tiene puntas.',
        choices: [
          shapeCard('triangle', 0.38, false),
          shapeCard('triangle', 0.24, false),
          shapeCard('circle', 0.3, true),
          shapeCard('triangle', 0.31, false),
        ],
      },
    ];
  }
}
