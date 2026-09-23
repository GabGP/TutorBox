// Módulo 3 · Todos, Algunos, Ninguno
// CNB Primero, competencia 3 — 3.2.1 (todos, algunos, ninguno) y 3.1.1 (identificación de conjuntos).
import { ChoiceLesson } from '../shared/choice-lesson.js';
import { drawBasket, drawEmoji, drawItems } from '../shared/draw.js';
import { mango, banano, naranja, tomate, aguacate, elote, gallina, vaca, cerdo } from '../shared/art.js';

const basketOf = (items) => (ctx, box) => {
  drawBasket(ctx, { x: box.x, y: box.y + box.h * 0.35, w: box.w, h: box.h * 0.6 });
  drawItems(ctx, items, items.length, { x: box.x, y: box.y + box.h * 0.05, w: box.w, h: box.h * 0.55 });
};

// Three baskets: all of `thing`, some of it, none of it. `want` says which one is right.
function baskets(thing, other, want) {
  const sets = {
    todos: [thing, thing, thing, thing],
    algunos: [thing, other, thing, other],
    ninguno: [other, other, other, other],
  };
  return Object.entries(sets).map(([kind, items]) => ({ correct: kind === want, draw: basketOf(items) }));
}

const emojiCard = (emoji, correct, hint) => ({
  correct,
  hint,
  draw: (ctx, box) => drawEmoji(ctx, emoji, box.x + box.w / 2, box.y + box.h / 2, Math.min(box.w, box.h) * 0.7),
});

export default class TodosAlgunosNingunoLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a mirar las canastas del mercado!'; }
  get colors() { return ['#FFF8E1', '#FFE0B2']; }

  makeRounds() {
    return [
      {
        say: '¿En qué canasta TODAS las frutas son mangos?',
        ask: '¿Dónde todas son mangos?',
        hint: 'Busca la canasta donde no hay ninguna otra fruta.',
        choices: baskets(mango, banano, 'todos'),
      },
      {
        say: '¿En qué canasta NO hay NINGÚN tomate?',
        ask: '¿Dónde no hay ningún tomate?',
        hint: 'Ninguno quiere decir que no hay ni uno.',
        choices: baskets(tomate, aguacate, 'ninguno'),
      },
      {
        say: '¿En qué canasta ALGUNAS frutas son naranjas, pero no todas?',
        ask: '¿Dónde algunas son naranjas?',
        hint: 'Busca la canasta que tiene naranjas y también otra fruta.',
        choices: baskets(naranja, banano, 'algunos'),
      },
      {
        say: 'Estos son animales de la granja. ¿Cuál NO es un animal?',
        ask: '¿Cuál no es un animal?',
        choices: [
          emojiCard(gallina, false, 'La gallina sí es un animal. Busca otro.'),
          emojiCard(vaca, false, 'La vaca sí es un animal. Busca otro.'),
          emojiCard(elote, true),
          emojiCard(cerdo, false, 'El cerdo sí es un animal. Busca otro.'),
        ],
      },
    ];
  }
}
