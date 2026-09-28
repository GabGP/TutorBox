// Nivel 6 · Cubos y Prismas
// CNB Tercero, competencia 6 — 6.1.7 (sólidos por el tipo y número de caras) y 6.1.6
// (características del cubo y los prismas rectangulares). Las respuestas salen de la tabla SOLIDS.
import { ChoiceLesson, numberChoices, stacked } from '../shared/choice-lesson.js';
import { center, drawShape } from '../shared/draw.js';

const EDGE = '#6D4C41';

function paint(ctx, path, fill) {
  ctx.fillStyle = fill;
  ctx.strokeStyle = EDGE;
  ctx.lineWidth = 3;
  ctx.lineJoin = 'round';
  ctx.beginPath(); path(); ctx.fill(); ctx.stroke();
}

function box3d(w, h, d) {
  return (ctx, cx, cy) => {
    const [x, y] = [cx - w / 2 - d / 2, cy - h / 2 + d / 2];
    paint(ctx, () => ctx.rect(x, y, w, h), '#FFCC80');
    paint(ctx, () => { ctx.moveTo(x, y); ctx.lineTo(x + d, y - d); ctx.lineTo(x + w + d, y - d); ctx.lineTo(x + w, y); ctx.closePath(); }, '#FFE0B2');
    paint(ctx, () => { ctx.moveTo(x + w, y); ctx.lineTo(x + w + d, y - d); ctx.lineTo(x + w + d, y + h - d); ctx.lineTo(x + w, y + h); ctx.closePath(); }, '#FFB74D');
  };
}

function piramide(ctx, cx, cy, r) {
  const top = [cx, cy - r * 0.9];
  const [fl, fr, br] = [[cx - r * 0.9, cy + r * 0.6], [cx + r * 0.4, cy + r * 0.8], [cx + r * 0.9, cy + r * 0.35]];
  paint(ctx, () => { ctx.moveTo(...top); ctx.lineTo(...fl); ctx.lineTo(...fr); ctx.closePath(); }, '#FFCC80');
  paint(ctx, () => { ctx.moveTo(...top); ctx.lineTo(...fr); ctx.lineTo(...br); ctx.closePath(); }, '#FFB74D');
}

// faces, vertices (esquinas), edges (aristas) and the flat figure of its side faces.
const SOLIDS = {
  cubo: { draw: (ctx, cx, cy, r) => box3d(r * 1.1, r * 1.1, r * 0.55)(ctx, cx, cy), faces: 6, vertices: 8, edges: 12, sides: 'cuadrado' },
  prisma: { draw: (ctx, cx, cy, r) => box3d(r * 1.5, r * 0.8, r * 0.45)(ctx, cx, cy), faces: 6, vertices: 8, edges: 12, sides: 'rectángulo' },
  piramide: { draw: piramide, faces: 5, vertices: 5, edges: 8, sides: 'triángulo' },
};
const FLAT = { cuadrado: 'square', rectángulo: 'rectangle', triángulo: 'triangle', círculo: 'circle' };

const solid = (name) => (ctx, box) => {
  const { cx, cy } = center(box);
  SOLIDS[name].draw(ctx, cx, cy, Math.min(box.w, box.h) * 0.42);
};
const flat = (name) => (ctx, box) => drawShape(ctx, FLAT[name], box.x + box.w / 2, box.y + box.h / 2, Math.min(box.w, box.h) * 0.3, '#FFCC80');

export default class CubosPrismasLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a conocer cubos, cajas y pirámides!'; }
  get colors() { return ['#FFEBEE', '#FFF8E1']; }

  makeRounds() {
    return [
      {
        say: '¿Cuál de estos sólidos es un cubo? Todas sus caras son cuadrados iguales.',
        ask: '¿Cuál es el cubo?',
        hint: 'El cubo es como un dado: todas sus caras son iguales.',
        choices: stacked(['prisma', 'cubo', 'piramide'].map((n) => ({ correct: SOLIDS[n].sides === 'cuadrado', draw: solid(n) }))),
      },
      {
        say: '¿Cuántas caras tiene el cubo?',
        ask: '¿Cuántas caras tiene el cubo?',
        hint: 'Arriba, abajo, adelante, atrás y los dos lados.',
        scene: solid('cubo'),
        choices: numberChoices(SOLIDS.cubo.faces, { max: 12 }),
      },
      {
        say: '¿Qué figura plana forma cada cara del cubo?',
        ask: '¿Qué forma tienen sus caras?',
        hint: 'Las caras del cubo tienen 4 lados iguales.',
        scene: solid('cubo'),
        choices: ['cuadrado', 'rectángulo', 'triángulo'].map((f) => ({ value: f, correct: f === SOLIDS.cubo.sides, draw: flat(f) })),
      },
      {
        say: 'Esta caja es un prisma rectangular. ¿Cuántos vértices, o esquinas, tiene?',
        ask: '¿Cuántos vértices tiene la caja?',
        hint: 'Cuenta las esquinas de arriba y después las de abajo.',
        scene: solid('prisma'),
        choices: numberChoices(SOLIDS.prisma.vertices, { max: 12 }),
      },
      {
        say: 'La pirámide tiene la base cuadrada. ¿Qué figura forman sus otras caras?',
        ask: '¿Qué forma tienen sus otras caras?',
        hint: 'Las caras de los lados terminan en la punta.',
        scene: solid('piramide'),
        choices: ['triángulo', 'cuadrado', 'círculo'].map((f) => ({ value: f, correct: f === SOLIDS.piramide.sides, draw: flat(f) })),
      },
      {
        say: '¿Cuántas aristas, los bordes rectos, tiene el cubo?',
        ask: '¿Cuántas aristas tiene el cubo?',
        hint: '4 arriba, 4 abajo y 4 de pie.',
        scene: solid('cubo'),
        choices: numberChoices(SOLIDS.cubo.edges, { max: 20 }),
      },
    ];
  }
}
