// Nivel 1 · ¿Cuál es Diferente?
// CNB Segundo, competencia 1 — 1.1.1 (diferencias entre patrones de la naturaleza y de la cultura).
// Tres tiras: dos siguen su patrón y una lo rompe. Las tiras correctas usan patrones distintos,
// así el niño tiene que pensar en la regla y no solo buscar la figura cambiada.
import { ChoiceLesson } from '../shared/choice-lesson.js';
import { drawEmoji, drawShape } from '../shared/draw.js';
import { aguacate, banano, elote, naranja, tomate } from '../shared/art.js';

const S = (kind, color) => ({ kind, color });
const LEN = 6;

// Repeats `unit` down the strip; at index `broken` it puts the piece that should come next instead.
function strip(unit, broken = -1) {
  return Array.from({ length: LEN }, (_, i) => unit[(i === broken ? i + 1 : i) % unit.length]);
}

function drawStrip(ctx, box, seq) {
  ctx.fillStyle = '#FFF8E1';
  ctx.beginPath(); ctx.roundRect(box.x + box.w * 0.12, box.y, box.w * 0.76, box.h, 10); ctx.fill();
  const cell = box.h / seq.length;
  seq.forEach((p, i) => {
    const cx = box.x + box.w / 2;
    const cy = box.y + cell * (i + 0.5);
    const size = Math.min(cell * 1.05, box.w * 0.7);
    if (typeof p === 'function') drawEmoji(ctx, p, cx, cy, size);
    else drawShape(ctx, p.kind, cx, cy, size * 0.42, p.color);
  });
}

const ROUNDS = [
  {
    say: 'Mira las tres tiras de tejido. Una tiene un error en su patrón. ¿Cuál es?',
    good: [[S('circle', '#E53935'), S('triangle', '#1E88E5')], [S('square', '#43A047'), S('square', '#FDD835')]],
    bad: [[S('triangle', '#6A1B9A'), S('circle', '#FB8C00')], 3],
  },
  {
    say: 'En la milpa sembraron en filas. ¿Qué fila NO sigue su patrón?',
    good: [[elote, elote, tomate], [aguacate, elote]],
    bad: [[tomate, aguacate], 2],
  },
  {
    say: 'En el mercado ordenaron la fruta. ¿Qué fila tiene un error?',
    good: [[tomate, banano, naranja], [naranja, naranja, elote]],
    bad: [[banano, tomate], 4],
  },
  {
    say: 'Mira estos tejidos de colores. ¿Cuál se equivocó?',
    good: [[S('circle', '#E53935'), S('circle', '#E53935'), S('circle', '#1E88E5')], [S('triangle', '#FDD835'), S('triangle', '#43A047')]],
    bad: [[S('square', '#6A1B9A'), S('square', '#FB8C00'), S('square', '#1E88E5')], 1],
  },
];

export default class PatronDiferenteLesson extends ChoiceLesson {
  get intro() { return '¡A buscar errores en los patrones!'; }
  get colors() { return ['#F3E5F5', '#E8F5E9']; }

  makeRounds() {
    return ROUNDS.map(({ say, good, bad: [unit, at] }) => ({
      say,
      ask: '¿Qué tira NO sigue su patrón?',
      hint: 'Mira cada tira de arriba hacia abajo y di su patrón en voz alta.',
      choices: [
        ...good.map((u) => ({ correct: false, draw: (ctx, box) => drawStrip(ctx, box, strip(u)) })),
        { correct: true, draw: (ctx, box) => drawStrip(ctx, box, strip(unit, at)) },
      ],
    }));
  }
}
