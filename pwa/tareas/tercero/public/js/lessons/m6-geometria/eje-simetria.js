// Nivel 6 · Ejes de Simetría
// CNB Tercero, competencia 6 — 6.3.1 (identificación del eje de simetría en figuras planas y
// objetos de su entorno). Una línea es eje si al reflejar cada esquina sobre ella se cae en otra
// esquina: se comprueba en código, no a mano.
import { ChoiceLesson, numberChoices, pickChoices, stacked } from '../shared/choice-lesson.js';

const reflect = ([x, y], [[ax, ay], [bx, by]]) => {
  const [dx, dy] = [bx - ax, by - ay];
  const t = ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy);
  return [2 * (ax + t * dx) - x, 2 * (ay + t * dy) - y];
};
const near = (p, q) => Math.abs(p[0] - q[0]) < 1e-6 && Math.abs(p[1] - q[1]) < 1e-6;
const isAxis = (poly, line) => poly.every((p) => poly.some((q) => near(reflect(p, line), q)));
const middle = (poly) => [0, 1].map((k) => poly.reduce((s, p) => s + p[k], 0) / poly.length);
// Every line through the middle, one each 15 degrees, that is an axis.
const axes = (poly) => {
  const [cx, cy] = middle(poly);
  return Array.from({ length: 12 }, (_, i) => [[cx, cy], [cx + Math.cos((i * Math.PI) / 12), cy + Math.sin((i * Math.PI) / 12)]])
    .filter((l) => isAxis(poly, l));
};

// Figures in grid units, y growing down.
const HOUSE = [[0, 2], [2, 0], [4, 2], [4, 5], [0, 5]];
const RECT = [[0, 0], [6, 0], [6, 3], [0, 3]];
const SQUARE = [[0, 0], [4, 0], [4, 4], [0, 4]];
const ISOSCELES = [[0, 4], [2, 0], [4, 4]];
const PARALLELOGRAM = [[1, 0], [5, 0], [4, 3], [0, 3]];

function draw(poly, line = null) {
  return (ctx, box) => {
    const xs = poly.map((p) => p[0]);
    const ys = poly.map((p) => p[1]);
    const [x0, y0] = [Math.min(...xs), Math.min(...ys)];
    const [w, h] = [Math.max(...xs) - x0, Math.max(...ys) - y0];
    const s = Math.min((box.w * 0.7) / w, (box.h * 0.7) / h);
    const P = ([x, y]) => [box.x + (box.w - w * s) / 2 + (x - x0) * s, box.y + (box.h - h * s) / 2 + (y - y0) * s];
    ctx.save();
    ctx.fillStyle = '#90CAF9';
    ctx.strokeStyle = '#1565C0';
    ctx.lineWidth = 3;
    ctx.beginPath(); poly.forEach((p) => ctx.lineTo(...P(p))); ctx.closePath(); ctx.fill(); ctx.stroke();
    if (line) {
      const [[ax, ay], [bx, by]] = line;
      const k = (w + h) / Math.hypot(bx - ax, by - ay);
      ctx.beginPath(); ctx.rect(box.x, box.y, box.w, box.h); ctx.clip();
      ctx.setLineDash([8, 6]);
      ctx.strokeStyle = '#D32F2F';
      ctx.beginPath(); ctx.moveTo(...P([ax - (bx - ax) * k, ay - (by - ay) * k])); ctx.lineTo(...P([ax + (bx - ax) * k, ay + (by - ay) * k])); ctx.stroke();
    }
    ctx.restore();
  };
}

function whichLine(poly, lines, say, place = null) {
  const choices = lines.map((l) => ({ correct: isAxis(poly, l), draw: draw(poly, l) }));
  return {
    say,
    ask: '¿Dónde está el eje de simetría?',
    hint: 'Si doblas la figura por el eje, las dos mitades quedan una encima de la otra.',
    choices: place ? stacked(choices) : choices,
  };
}

export default class EjeSimetriaLesson extends ChoiceLesson {
  get intro() { return '¡Un eje de simetría parte una figura en dos mitades iguales!'; }
  get colors() { return ['#FFEBEE', '#F3E5F5']; }

  makeRounds() {
    const rectAxes = axes(RECT).length;
    const shapes = [ISOSCELES, RECT, PARALLELOGRAM];
    return [
      whichLine(HOUSE, [[[2, 0], [2, 5]], [[0, 3], [4, 3]], [[0, 0], [4, 5]]],
        'Mira la casita. ¿En qué dibujo la línea roja es un eje de simetría?'),
      whichLine(RECT, [[[0, 0], [6, 3]], [[0, 1.5], [6, 1.5]], [[2, 0], [2, 3]]],
        'Ahora el rectángulo. ¿En cuál la línea roja es un eje de simetría?', 'stacked'),
      {
        say: '¿Cuántos ejes de simetría tiene el cuadrado?',
        ask: '¿Cuántos ejes tiene el cuadrado?',
        hint: 'Puedes doblarlo de arriba abajo, de lado a lado, y por las dos diagonales.',
        scene: draw(SQUARE),
        choices: numberChoices(axes(SQUARE).length, { max: 9 }),
      },
      {
        say: '¿Y cuántos ejes de simetría tiene este rectángulo? ¡Cuidado con las diagonales!',
        ask: '¿Cuántos ejes tiene el rectángulo?',
        hint: 'Si lo doblas por la diagonal, las mitades no coinciden.',
        scene: draw(RECT),
        choices: pickChoices(rectAxes, [axes(SQUARE).length, rectAxes - 1]),
      },
      {
        say: '¿Qué figura NO tiene ningún eje de simetría?',
        ask: '¿Cuál no tiene eje de simetría?',
        hint: 'Prueba doblar cada figura en tu mente. En una, ningún doblez funciona.',
        choices: shapes.map((poly) => ({ correct: axes(poly).length === 0, draw: draw(poly) })),
      },
    ];
  }
}
