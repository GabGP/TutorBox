// Nivel 3 · Subconjuntos
// CNB Segundo, competencia 3 — 3.2.1 (descripción y formación de subconjuntos de un conjunto).
import { ChoiceLesson, numberChoices } from '../shared/choice-lesson.js';
import { aguacate, banano, gallina, mango, tomate } from '../shared/art.js';
import { drawSet } from './pertenece.js';

// The market basket: how many of each fruit it holds.
const SET = [[mango, 3], [aguacate, 2], [banano, 4]];
const ALL = SET.flatMap(([art, n]) => Array(n).fill(art));
const count = (...arts) => SET.filter(([a]) => arts.includes(a)).reduce((sum, [, n]) => sum + n, 0);
const scene = (ctx, box) => drawSet(ctx, box, ALL);

// A small group of things; it is a subset only if every thing in it is in SET.
function group(arts) {
  return {
    correct: arts.every((a) => count(a) > 0),
    draw: (ctx, box) => drawSet(ctx, box, arts),
  };
}

function howMany(say, arts, hint) {
  return {
    say,
    ask: '¿Cuántos tiene el subconjunto?',
    hint,
    scene,
    choices: numberChoices(count(...arts), { max: ALL.length }),
  };
}

export default class SubconjuntosLesson extends ChoiceLesson {
  get intro() { return '¡Un subconjunto es una parte del conjunto!'; }
  get colors() { return ['#FFF3E0', '#FFFDE7']; }

  makeRounds() {
    return [
      howMany('Formamos un subconjunto solo con los mangos. ¿Cuántos elementos tiene?', [mango], 'Cuenta solo los mangos.'),
      howMany('Ahora un subconjunto con las frutas largas y amarillas: los bananos. ¿Cuántos tiene?', [banano], 'Cuenta solo los bananos.'),
      {
        say: '¿Cuál grupo es un subconjunto de la canasta? Todas sus cosas deben estar en la canasta.',
        ask: '¿Cuál es un subconjunto?',
        hint: 'Busca en la canasta cada cosa del grupo. Si una no está, no es subconjunto.',
        scene,
        choices: [group([mango, aguacate]), group([mango, tomate]), group([gallina, banano])],
      },
      howMany('Un subconjunto con los mangos y los aguacates. ¿Cuántos elementos tiene?', [mango, aguacate], 'Cuenta los mangos y después sigue contando los aguacates.'),
    ];
  }
}
