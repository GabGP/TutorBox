// Nivel 6 · Perímetro en Centímetros
// CNB Segundo, competencia 6 — 6.2.1 (perímetro de triángulo, cuadrado y rectángulo con metro y
// centímetro) y 6.3.2 (triángulos y cuadriláteros en hoja cuadriculada).
// Distractores: el área en vez del perímetro (5 × 2) o sumar solo dos lados.
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { drawText } from '../shared/draw.js';

const COLS = 8;
const ROWS = 5;
const cm = (ctx, value, box) => drawText(ctx, `${value} cm`, box);

const lengths = (pts) => pts.map((p, i) => {
  const q = pts[(i + 1) % pts.length];
  return Math.hypot(q[0] - p[0], q[1] - p[1]);
});

/** Squared paper (1 square = 1 cm) with the figure on it and each side labelled. */
function paper(ctx, box, pts) {
  const c = Math.min(box.w / (COLS + 1), box.h / (ROWS + 1));
  const x0 = box.x + (box.w - c * COLS) / 2;
  const y0 = box.y + (box.h - c * ROWS) / 2;
  const P = ([x, y]) => [x0 + (x + 1) * c, y0 + (y + 1) * c];
  ctx.save();
  ctx.strokeStyle = 'rgba(33,150,243,0.3)';
  ctx.lineWidth = 1;
  for (let i = 0; i <= COLS; i++) { ctx.beginPath(); ctx.moveTo(x0 + i * c, y0); ctx.lineTo(x0 + i * c, y0 + ROWS * c); ctx.stroke(); }
  for (let j = 0; j <= ROWS; j++) { ctx.beginPath(); ctx.moveTo(x0, y0 + j * c); ctx.lineTo(x0 + COLS * c, y0 + j * c); ctx.stroke(); }
  ctx.fillStyle = 'rgba(239,154,154,0.6)';
  ctx.strokeStyle = '#C62828';
  ctx.lineWidth = 4;
  ctx.beginPath(); pts.forEach((p) => ctx.lineTo(...P(p))); ctx.closePath(); ctx.fill(); ctx.stroke();
  const [mx, my] = pts.reduce(([sx, sy], [x, y]) => [sx + x / pts.length, sy + y / pts.length], [0, 0]);
  ctx.fillStyle = '#1F2A1F';
  ctx.font = `bold ${Math.round(c * 0.42)}px Nunito, sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  lengths(pts).forEach((len, i) => {
    const [a, b] = [pts[i], pts[(i + 1) % pts.length]];
    const [x, y] = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
    const [dx, dy] = [x - mx, y - my];
    const d = Math.hypot(dx, dy) || 1;
    const [px, py] = P([x + (dx / d) * 0.55, y + (dy / d) * 0.55]);
    ctx.fillText(`${len} cm`, px, py);
  });
  ctx.restore();
}

const rect = (w, h) => [[0, 0], [w, 0], [w, h], [0, h]];

function perimeter(pts, say) {
  const sides = lengths(pts);
  const total = sides.reduce((a, b) => a + b, 0);
  const [w, h] = sides;
  return {
    say,
    ask: '¿Cuánto mide el perímetro?',
    hint: 'El perímetro es la vuelta completa. Suma todos los lados.',
    scene: (ctx, box) => paper(ctx, box, pts),
    choices: pickChoices(total, pts.length === 4 ? [w * h, w + h] : [w + h, total + 1], { draw: cm }),
  };
}

export default class PerimetroCmLesson extends ChoiceLesson {
  get intro() { return '¡Cada cuadrito de la hoja mide un centímetro!'; }
  get colors() { return ['#FFEBEE', '#E3F2FD']; }

  makeRounds() {
    return [
      perimeter(rect(3, 3), 'Este cuadrado está dibujado en la hoja cuadriculada. ¿Cuánto mide su perímetro, la vuelta completa?'),
      perimeter(rect(5, 2), 'Ahora un rectángulo. ¿Cuánto mide su perímetro?'),
      perimeter([[0, 0], [4, 0], [0, 3]], 'Ahora un triángulo. Suma sus tres lados. ¿Cuánto mide su perímetro?'),
      perimeter(rect(6, 2), 'Don Luis hace un marco para una foto. ¿Cuántos centímetros de madera necesita para dar la vuelta?'),
    ];
  }
}
