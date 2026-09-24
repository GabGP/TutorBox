// Nivel 5 · Prueba y Piensa
// CNB Segundo, competencia 5 — 5.2.1 (estrategias de ensayo y error), 5.3.1 y 5.3.2 (seguir
// instrucciones y razonamiento lógico en juegos) y 5.4.1 (predecir lo que puede ocurrir).
// Ensayo y error: cada respuesta equivocada le dice al niño qué resultado da su prueba.
import { ChoiceLesson } from '../shared/choice-lesson.js';
import { drawEmoji, drawNumeral, drawShape } from '../shared/draw.js';
import { cerdo, gallina, vaca } from '../shared/art.js';

// The child tries each number; a wrong try says what it really gives.
function guess({ say, ask, rule, target, candidates }) {
  return {
    say,
    ask,
    choices: candidates.map((v) => ({
      value: v,
      correct: rule(v) === target,
      hint: `Prueba con ${v}: da ${rule(v)}, no ${target}. Prueba otro.`,
      draw: (ctx, box) => drawNumeral(ctx, v, box),
    })),
  };
}

const picture = (item) => (ctx, box) => drawEmoji(ctx, item, box.x + box.w / 2, box.y + box.h / 2, Math.min(box.w, box.h) * 0.75);
const figure = (kind, color) => (ctx, box) => drawShape(ctx, kind, box.x + box.w / 2, box.y + box.h / 2, Math.min(box.w, box.h) * 0.35, color);

// Heaviest to lightest.
const BY_WEIGHT = [vaca, cerdo, gallina];

export default class PiensaResuelveLesson extends ChoiceLesson {
  get intro() { return '¡A pensar como detectives!'; }
  get colors() { return ['#EFEBE9', '#E3F2FD']; }

  makeRounds() {
    const [add, total] = [4, 10];
    const lightest = BY_WEIGHT[BY_WEIGHT.length - 1];
    const figures = [['circle', '#E53935', 'rojo'], ['circle', '#1E88E5', 'azul'], ['triangle', '#1E88E5', 'azul']];
    return [
      guess({
        say: `Pienso en un número. Si le sumo ${add}, me da ${total}. ¿Qué número pensé? Prueba cada uno.`,
        ask: `? + ${add} = ${total}`,
        rule: (v) => v + add,
        target: total,
        candidates: [total - add, total + add, add],
      }),
      guess({
        say: 'Dos bolsas tienen el mismo número de jocotes. Entre las dos hay 12. ¿Cuántos hay en cada bolsa?',
        ask: '? + ? = 12',
        rule: (v) => v + v,
        target: 12,
        candidates: [6, 10, 4],
      }),
      {
        say: 'La vaca pesa más que el cerdo. El cerdo pesa más que la gallina. ¿Quién pesa MENOS?',
        ask: '¿Quién pesa menos?',
        hint: 'Si el cerdo pesa más que la gallina, y la vaca más que el cerdo, ¿quién es el más liviano?',
        choices: BY_WEIGHT.map((a) => ({ correct: a === lightest, draw: picture(a) })),
      },
      {
        say: 'Hay nubes negras y se oyen truenos. ¿Qué va a pasar?',
        ask: '¿Qué va a pasar?',
        hint: 'Las nubes negras y los truenos avisan que viene algo...',
        choices: [picture('🌧️'), picture('☀️'), picture('🌙')].map((draw, i) => ({ correct: i === 0, draw })),
      },
      {
        say: 'Sigue la instrucción: toca la figura que NO es roja y NO es un círculo.',
        ask: 'Ni roja, ni círculo',
        hint: 'Quita las rojas. Después quita los círculos. ¿Cuál queda?',
        choices: figures.map(([kind, color, name]) => ({ correct: name !== 'rojo' && kind !== 'circle', draw: figure(kind, color) })),
      },
    ];
  }
}
