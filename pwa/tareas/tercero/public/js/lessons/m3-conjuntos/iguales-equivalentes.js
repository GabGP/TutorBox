// Nivel 3 · Conjuntos Iguales y Equivalentes
// CNB Tercero, competencia 3 — 3.2.1 (identificación de conjuntos iguales y equivalentes).
// Iguales: los mismos elementos. Equivalentes: la misma cantidad de elementos. La relación se
// calcula con sameSet y la cantidad, nunca a mano.
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { aguacate, banano, cerdo, elote, gallina, mango, pollito, tomate, vaca } from '../shared/art.js';
import { drawSet } from './vacio-unitario.js';

const RELATIONS = ['iguales', 'equivalentes', 'ninguno'];
const sameSet = (a, b) => a.length === b.length && a.every((x) => b.includes(x));
const relation = (a, b) => (sameSet(a, b) ? 'iguales' : a.length === b.length ? 'equivalentes' : 'ninguno');

function pairScene(a, b) {
  return (ctx, box) => {
    const half = { ...box, w: box.w / 2 };
    drawSet(ctx, half, a, { label: 'A' });
    drawSet(ctx, { ...half, x: box.x + box.w / 2 }, b, { label: 'B' });
  };
}

function howAre(a, b) {
  return {
    say: 'Mira los conjuntos A y B. ¿Son iguales, equivalentes, o ninguno de los dos?',
    ask: '¿Cómo son A y B?',
    hint: 'Iguales: tienen los mismos elementos. Equivalentes: la misma cantidad, pero otras cosas.',
    scene: pairScene(a, b),
    choices: pickChoices(relation(a, b), RELATIONS),
  };
}

export default class IgualesEquivalentesLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a comparar conjuntos del mercado!'; }
  get colors() { return ['#FFF3E0', '#E8F5E9']; }

  makeRounds() {
    const A = [mango, banano, tomate];
    const sceneA = (ctx, box) => drawSet(ctx, box, A, { label: 'A' });
    return [
      {
        say: '¿Cuál conjunto es IGUAL al conjunto A? Debe tener exactamente los mismos elementos.',
        ask: '¿Cuál es igual al conjunto A?',
        hint: 'Busca los mismos elementos, aunque estén en otro orden.',
        scene: sceneA,
        choices: [[tomate, mango, banano], [gallina, vaca, cerdo], [mango, banano]]
          .map((s) => ({ correct: relation(A, s) === 'iguales', draw: (ctx, box) => drawSet(ctx, box, s) })),
      },
      {
        say: '¿Cuál conjunto es EQUIVALENTE al A, pero no igual? Tiene la misma cantidad, con otras cosas.',
        ask: '¿Cuál es equivalente al A?',
        hint: 'Cuenta los elementos de A. Busca otro conjunto con esa misma cantidad.',
        scene: sceneA,
        choices: [[elote, aguacate, pollito], [mango, banano, tomate, elote], [aguacate]]
          .map((s) => ({ correct: relation(A, s) === 'equivalentes', draw: (ctx, box) => drawSet(ctx, box, s) })),
      },
      howAre([gallina, vaca, cerdo], [pollito, gallina, vaca]),
      howAre([elote, tomate], [tomate, elote]),
      howAre([banano, aguacate, mango, tomate], [vaca, cerdo]),
    ];
  }
}
