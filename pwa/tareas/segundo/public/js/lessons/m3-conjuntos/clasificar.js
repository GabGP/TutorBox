// Nivel 3 · Clasificar con Dos o Tres Características
// CNB Segundo, competencia 3 — 3.3.1 (clasificación de conjuntos atendiendo 2 o 3 características).
// Las respuestas se cuentan de la lista de figuras, nunca se escriben a mano.
import { ChoiceLesson, numberChoices } from '../shared/choice-lesson.js';
import { drawShape } from '../shared/draw.js';

const COLOR = { rojo: '#E53935', azul: '#1E88E5', amarillo: '#FDD835' };
const F = (kind, color, big) => ({ kind, color, big });

const FIGS = [
  F('triangle', 'rojo', true), F('circle', 'azul', false), F('square', 'rojo', false),
  F('circle', 'rojo', true), F('triangle', 'azul', true), F('square', 'amarillo', true),
  F('triangle', 'rojo', false), F('circle', 'azul', true), F('triangle', 'amarillo', false),
];

const figure = (f) => (ctx, box) => {
  const r = Math.min(box.w, box.h) * (f.big ? 0.4 : 0.22);
  drawShape(ctx, f.kind, box.x + box.w / 2, box.y + box.h / 2, r, COLOR[f.color]);
};

function scene(ctx, box) {
  const cell = { w: box.w / 3, h: box.h / 3 };
  FIGS.forEach((f, i) => figure(f)(ctx, { x: box.x + (i % 3) * cell.w, y: box.y + Math.floor(i / 3) * cell.h, ...cell }));
}

function howMany(say, ask, test, hint) {
  return { say, ask, hint, scene, choices: numberChoices(FIGS.filter(test).length, { max: FIGS.length }) };
}

export default class ClasificarLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a clasificar figuras mirando varias cosas a la vez!'; }
  get colors() { return ['#FFF3E0', '#E3F2FD']; }

  makeRounds() {
    const target = F('square', 'rojo', false);
    return [
      howMany('Mira bien. ¿Cuántas figuras son triángulos y además rojas?', '¿Cuántos triángulos rojos?',
        (f) => f.kind === 'triangle' && f.color === 'rojo', 'Busca los triángulos. De ellos, cuenta solo los rojos.'),
      howMany('¿Cuántas figuras son azules y grandes?', '¿Cuántas azules y grandes?',
        (f) => f.color === 'azul' && f.big, 'Busca las azules. De ellas, cuenta solo las grandes.'),
      howMany('Ahora tres cosas a la vez. ¿Cuántas son círculos, azules y pequeños?', '¿Cuántos círculos azules pequeños?',
        (f) => f.kind === 'circle' && f.color === 'azul' && !f.big, 'Tiene que ser círculo, ser azul y ser pequeño, las tres cosas.'),
      {
        say: '¿Cuál figura es un cuadrado, rojo y pequeño?',
        ask: '¿Cuál es cuadrado, rojo y pequeño?',
        hint: 'Revisa las tres cosas: la forma, el color y el tamaño.',
        choices: [target, F('square', 'rojo', true), F('square', 'amarillo', false), F('triangle', 'rojo', false)].map((f) => ({
          correct: f.kind === target.kind && f.color === target.color && f.big === target.big,
          draw: figure(f),
        })),
      },
    ];
  }
}
