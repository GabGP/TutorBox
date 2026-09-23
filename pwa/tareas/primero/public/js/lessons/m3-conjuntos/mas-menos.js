// Módulo 3 · Más o Menos
// CNB Primero 3.2.1 (muchos, pocos, tantos como) y 3.3.1 (correspondencia uno a uno: mayor, menor, igual).
import { ChoiceLesson } from '../shared/choice-lesson.js';
import { drawBasket, drawItems } from '../shared/draw.js';
import { mango, banano, tomate, pollito } from '../shared/art.js';

const basketOf = (item, n, slots = n) => (ctx, box) => {
  drawBasket(ctx, { x: box.x, y: box.y + box.h * 0.35, w: box.w, h: box.h * 0.6 });
  drawItems(ctx, item, n, { x: box.x, y: box.y + box.h * 0.05, w: box.w, h: box.h * 0.55 }, { slots });
};

// The right basket is found from the counts (more / fewer / same), never marked by hand.
function compare(item, counts, want) {
  const target = want === 'more' ? Math.max(...counts) : want === 'fewer' ? Math.min(...counts) : want;
  const slots = Math.max(...counts);
  return counts.map((n) => ({ correct: n === target, draw: basketOf(item, n, slots) }));
}

export default class MasMenosLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a comparar canastas!'; }
  get colors() { return ['#FFF8E1', '#FFE0B2']; }

  makeRounds() {
    return [
      {
        say: '¿Qué canasta tiene MÁS mangos?',
        ask: '¿Dónde hay más mangos?',
        hint: 'Cuenta los mangos de cada canasta y compara.',
        choices: compare(mango, [5, 2], 'more'),
      },
      {
        say: '¿Qué canasta tiene MENOS tomates?',
        ask: '¿Dónde hay menos tomates?',
        hint: 'La que tiene menos es la que tiene pocos.',
        choices: compare(tomate, [3, 6], 'fewer'),
      },
      {
        say: 'Mira esta canasta de bananos. ¿Cuál canasta de abajo tiene TANTOS bananos como esta?',
        ask: '¿Cuál tiene tantos como esta?',
        hint: 'Junta un banano de arriba con uno de abajo. ¿Sobra alguno?',
        scene: basketOf(banano, 4, 4),
        choices: compare(banano, [4, 3], 4),
      },
      {
        say: '¿Dónde hay MÁS pollitos? Cuenta con cuidado.',
        ask: '¿Dónde hay más pollitos?',
        hint: 'Están casi iguales. Cuéntalos uno por uno.',
        choices: compare(pollito, [4, 5], 'more'),
      },
    ];
  }
}
