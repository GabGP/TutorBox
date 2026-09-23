// Módulo 6 · Construir Figuras
// CNB Primero 6.1.2 (clasificación por número de lados: triángulo y cuadriláteros) y 1.3.1 (líneas rectas y curvas).
import { ChoiceLesson, numberChoices } from '../shared/choice-lesson.js';
import { drawShape, drawSticks } from '../shared/draw.js';

// A closed figure drawn with `sides` sticks (triangle = 3, square = 4).
function stickFigure(ctx, box, sides) {
  const cx = box.x + box.w / 2;
  const cy = box.y + box.h * 0.55;
  const r = Math.min(box.w, box.h) * 0.36;
  const start = sides === 4 ? -Math.PI / 4 : -Math.PI / 2;
  ctx.strokeStyle = '#8D5524';
  ctx.lineWidth = 12;
  ctx.lineCap = 'round';
  for (let i = 0; i < sides; i++) {
    const a1 = start + (Math.PI * 2 * i) / sides;
    const a2 = start + (Math.PI * 2 * (i + 1)) / sides;
    ctx.beginPath();
    ctx.moveTo(cx + Math.cos(a1) * r, cy + Math.sin(a1) * r);
    ctx.lineTo(cx + Math.cos(a2) * r, cy + Math.sin(a2) * r);
    ctx.stroke();
  }
}

const sticks = (answer) => numberChoices(answer, { min: 2, max: 6, draw: (ctx, n, box) => drawSticks(ctx, n, box) });

const shapeCard = (kind, color, correct, hint) => ({
  correct,
  hint,
  draw: (ctx, box) => drawShape(ctx, kind, box.x + box.w / 2, box.y + box.h / 2, Math.min(box.w, box.h) * 0.34, color),
});

export default class ConstruirFormasLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a construir figuras con palitos!'; }
  get colors() { return ['#FBE9E7', '#FFF8E1']; }

  makeRounds() {
    return [
      {
        say: 'Mira este triángulo hecho con palitos. ¿Cuántos palitos necesitas para hacerlo?',
        ask: '¿Cuántos palitos tiene el triángulo?',
        hint: 'Cuenta los lados del triángulo: cada lado es un palito.',
        scene: (ctx, box) => stickFigure(ctx, box, 3),
        choices: sticks(3),
      },
      {
        say: 'Ahora un cuadrado. ¿Cuántos palitos necesitas?',
        ask: '¿Cuántos palitos tiene el cuadrado?',
        hint: 'Cuenta los lados del cuadrado, uno por uno.',
        scene: (ctx, box) => stickFigure(ctx, box, 4),
        choices: sticks(4),
      },
      {
        say: '¿Cuál figura NO tiene lados rectos?',
        ask: '¿Cuál no tiene lados rectos?',
        choices: [
          shapeCard('circle', '#FB8C00', true),
          shapeCard('triangle', '#43A047', false, 'El triángulo tiene tres lados rectos. Busca la figura redonda.'),
          shapeCard('square', '#1E88E5', false, 'El cuadrado tiene cuatro lados rectos. Busca la figura redonda.'),
        ],
      },
      {
        say: 'Toca la figura que tiene TRES lados.',
        ask: '¿Cuál tiene tres lados?',
        choices: [
          shapeCard('triangle', '#43A047', true),
          shapeCard('square', '#1E88E5', false, 'Ese es un cuadrado: tiene cuatro lados.'),
          shapeCard('rectangle', '#8E24AA', false, 'Ese es un rectángulo: tiene cuatro lados.'),
        ],
      },
    ];
  }
}
