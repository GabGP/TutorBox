// Nivel 2 · Caminos en el Plano
// CNB Segundo, competencia 2 — 2.2.1 (seguimiento de instrucciones para graficar movimientos
// dentro del primer cuadrante del plano cartesiano).
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { drawEmoji, drawQuq } from '../shared/draw.js';
import { cerdo, elote, gallina, mango, tomate } from '../shared/art.js';
import { drawThings } from './plano-puntos.js';

const THINGS = [
  { art: elote, x: 3, y: 2 },
  { art: mango, x: 2, y: 3 },
  { art: gallina, x: 1, y: 4 },
  { art: cerdo, x: 4, y: 1 },
  { art: tomate, x: 5, y: 4 },
];

const thingAt = (x, y) => THINGS.find((t) => t.x === x && t.y === y);

function scene(from) {
  return (ctx, box) => {
    const { at, cell } = drawThings(ctx, box, THINGS);
    drawQuq(ctx, at(from.x, from.y).x, at(from.x, from.y).y - cell * 0.1, cell * 1.1);
  };
}

// Q'uq' walks `right` then `up`; the wrong answers are where he lands if he swaps the two moves.
function walk(from, right, up) {
  const answer = thingAt(from.x + right, from.y + up);
  const others = [thingAt(from.x + up, from.y + right), ...THINGS]
    .filter((t, i, all) => t && t !== answer && all.indexOf(t) === i).slice(0, 2);
  return {
    say: `Q'uq' camina ${right} hacia la derecha y ${up} hacia arriba. ¿Qué encuentra?`,
    ask: `→ ${right}   ↑ ${up}   ¿Qué encuentra?`,
    hint: `Primero ${right} pasos a la derecha. Después ${up} hacia arriba. Cuenta las rayas.`,
    scene: scene(from),
    choices: [answer, ...others].map((t) => ({
      correct: t === answer,
      draw: (ctx, box) => drawEmoji(ctx, t.art, box.x + box.w / 2, box.y + box.h / 2, Math.min(box.w, box.h) * 0.8),
    })),
  };
}

const moves = (right, up) => `→${right}  ↑${up}`;

export default class PlanoCaminosLesson extends ChoiceLesson {
  get intro() { return '¡Ayuda a Q\'uq\' a caminar por la cuadrícula!'; }
  get colors() { return ['#E8F5E9', '#E1F5FE']; }

  makeRounds() {
    const origin = { x: 0, y: 0 };
    const target = THINGS[1];
    return [
      walk(origin, 3, 2),
      walk(origin, 1, 4),
      walk({ x: 1, y: 1 }, 3, 0),
      {
        say: 'Q\'uq\' quiere llegar al mango. ¿Qué camino debe seguir?',
        ask: '¿Qué camino lleva al mango?',
        hint: 'Cuenta cuántas rayas a la derecha está el mango, y cuántas hacia arriba.',
        scene: scene(origin),
        choices: pickChoices(moves(target.x, target.y), [moves(target.y, target.x), moves(target.x, target.x)]),
      },
    ];
  }
}
