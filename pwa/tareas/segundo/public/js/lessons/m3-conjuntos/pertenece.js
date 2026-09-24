// Nivel 3 · ¿Pertenece al Conjunto?
// CNB Segundo, competencia 3 — 3.1.1 (identificación de elementos que pertenecen y no pertenecen
// a un conjunto). Si pertenece o no se decide por la clase de cada cosa, no a mano.
import { ChoiceLesson } from '../shared/choice-lesson.js';
import { drawEmoji, drawShape } from '../shared/draw.js';
import { aguacate, banano, cerdo, elote, gallina, mango, naranja, pollito, tomate, vaca } from '../shared/art.js';

const shape = (kind, color) => (ctx, cx, cy, size) => drawShape(ctx, kind, cx, cy, size * 0.38, color);
const tri = (color) => shape('triangle', color);

const FRUTA = 'fruta';
const ANIMAL = 'animal';
const TRIANGULO = 'triángulo';
const AMARILLO = 'amarillo';
const is = (kind, ...arts) => arts.map((art) => ({ art, kind }));

/** The set drawn as a rope loop with its elements inside. */
export function drawSet(ctx, box, arts) {
  const { x, y, w, h } = box;
  ctx.save();
  ctx.strokeStyle = '#8D5524';
  ctx.lineWidth = 5;
  ctx.setLineDash([14, 6]);
  ctx.beginPath(); ctx.ellipse(x + w / 2, y + h / 2, w * 0.46, h * 0.44, 0, 0, Math.PI * 2); ctx.stroke();
  ctx.restore();
  // As many columns as suit the box's shape: a row in a wide scene, a column in a narrow card.
  const cols = Math.max(1, Math.min(arts.length, Math.round(Math.sqrt((arts.length * w) / h))));
  const rows = Math.ceil(arts.length / cols);
  const cell = Math.min((w * 0.7) / cols, (h * 0.66) / rows);
  arts.forEach((a, i) => {
    const inRow = Math.min(cols, arts.length - Math.floor(i / cols) * cols);
    const cx = x + w / 2 + ((i % cols) - (inRow - 1) / 2) * cell;
    const cy = y + h / 2 + (Math.floor(i / cols) - (rows - 1) / 2) * cell;
    drawEmoji(ctx, a, cx, cy, cell * 0.8);
  });
}

const ROUNDS = [
  { kind: FRUTA, set: [mango, banano, naranja], belongs: true, name: 'las frutas', options: [...is(FRUTA, aguacate), ...is(ANIMAL, vaca, pollito)] },
  { kind: ANIMAL, set: [gallina, vaca, cerdo], belongs: false, name: 'los animales de la granja', options: [...is(FRUTA, tomate), ...is(ANIMAL, pollito, gallina)] },
  {
    kind: TRIANGULO, set: [tri('#E53935'), tri('#1E88E5'), tri('#FDD835')], belongs: true, name: 'los triángulos',
    options: [...is(TRIANGULO, tri('#43A047')), ...is('círculo', shape('circle', '#43A047')), ...is('cuadrado', shape('square', '#E53935'))],
  },
  {
    kind: AMARILLO, set: [banano, elote, shape('circle', '#FDD835')], belongs: false, name: 'las cosas amarillas',
    options: [...is('verde', aguacate), ...is(AMARILLO, banano, shape('square', '#FDD835'))],
  },
];

export default class PerteneceLesson extends ChoiceLesson {
  get intro() { return '¡En el mercado juntamos las cosas en conjuntos!'; }
  get colors() { return ['#FFF3E0', '#FFFDE7']; }

  makeRounds() {
    return ROUNDS.map(({ kind, set, belongs, name, options }) => ({
      say: belongs
        ? `Este es el conjunto de ${name}. ¿Cuál SÍ pertenece a este conjunto?`
        : `Este es el conjunto de ${name}. ¿Cuál NO pertenece a este conjunto?`,
      ask: belongs ? '¿Cuál SÍ pertenece?' : '¿Cuál NO pertenece?',
      hint: `Piensa: ¿es parte de ${name}?`,
      scene: (ctx, box) => drawSet(ctx, box, set),
      choices: options.map((o) => ({
        correct: (o.kind === kind) === belongs,
        draw: (ctx, box) => drawEmoji(ctx, o.art, box.x + box.w / 2, box.y + box.h / 2, Math.min(box.w, box.h) * 0.8),
      })),
    }));
  }
}
