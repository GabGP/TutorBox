// Módulo 5 · La Granja en Gráfica
// CNB Primero, competencia 5 — 5.2.1 (recopilación de datos), 5.2.2 (conteo y representación
// gráfica de información recopilada) y 5.4.1 (descripción cuantitativa de eventos).
import { ChoiceLesson, numberChoices } from '../shared/choice-lesson.js';
import { drawEmoji } from '../shared/draw.js';
import { mango, banano, gallina, vaca, cerdo } from '../shared/art.js';

const FARM = [[gallina, 4], [vaca, 2], [cerdo, 3]];
const PICKED = [[mango, 3], [banano, 2]];

// A picture graph: one column per kind, one icon per thing counted, all on one baseline.
function pictograph(ctx, box, data) {
  const colW = box.w / data.length;
  const most = Math.max(...data.map(([, n]) => n), 1);
  const cell = Math.min(colW * 0.7, (box.h * 0.9) / most);
  const base = box.y + box.h * 0.95;
  ctx.strokeStyle = '#5D4037';
  ctx.lineWidth = 3;
  ctx.beginPath(); ctx.moveTo(box.x, base); ctx.lineTo(box.x + box.w, base); ctx.stroke();
  data.forEach(([emoji, n], c) => {
    const cx = box.x + colW * (c + 0.5);
    for (let i = 0; i < n; i++) drawEmoji(ctx, emoji, cx, base - cell * (i + 0.5), cell * 0.85);
  });
}

// The fruit the children picked, lying loose on the table before it is put in a graph.
function pile(ctx, box) {
  const spots = [[0.15, 0.3], [0.45, 0.6], [0.7, 0.25], [0.3, 0.75], [0.8, 0.7]];
  const items = PICKED.flatMap(([emoji, n]) => Array(n).fill(emoji));
  items.forEach((emoji, i) => {
    drawEmoji(ctx, emoji, box.x + box.w * spots[i][0], box.y + box.h * spots[i][1], box.h * 0.26);
  });
}

// The animal with the most / fewest, found from the data, never marked by hand.
function animalChoices(want) {
  const counts = FARM.map(([, n]) => n);
  const target = want === 'more' ? Math.max(...counts) : Math.min(...counts);
  return FARM.map(([emoji, n]) => ({
    correct: n === target,
    draw: (ctx, box) => drawEmoji(ctx, emoji, box.x + box.w / 2, box.y + box.h / 2, Math.min(box.w, box.h) * 0.7),
  }));
}

export default class GranjaGraficaLesson extends ChoiceLesson {
  get intro() { return '¡Contamos los animales de la granja y los pusimos en una gráfica!'; }
  get colors() { return ['#F1F8E9', '#FFF8E1']; }

  makeRounds() {
    const gallinas = FARM[0][1];
    const [mangos, bananos] = PICKED.map(([, n]) => n);
    const graphs = [[mangos, bananos], [bananos, mangos], [mangos, mangos]];
    return [
      {
        say: 'En la gráfica, cada dibujo es un animal. ¿Cuántas gallinas hay en la granja?',
        ask: '¿Cuántas gallinas hay?',
        hint: 'Cuenta las gallinas de su columna, de abajo hacia arriba.',
        scene: (ctx, box) => pictograph(ctx, box, FARM),
        choices: numberChoices(gallinas, { max: 9 }),
      },
      {
        say: 'Mira la gráfica. ¿De qué animal hay MÁS en la granja?',
        ask: '¿De qué animal hay más?',
        hint: 'La columna más alta es la que tiene más.',
        scene: (ctx, box) => pictograph(ctx, box, FARM),
        choices: animalChoices('more'),
      },
      {
        say: '¿Y de qué animal hay MENOS?',
        ask: '¿De qué animal hay menos?',
        hint: 'La columna más baja es la que tiene menos.',
        scene: (ctx, box) => pictograph(ctx, box, FARM),
        choices: animalChoices('fewer'),
      },
      {
        say: 'Juntamos estas frutas: mangos y bananos. ¿Qué gráfica muestra las frutas que juntamos?',
        ask: '¿Qué gráfica muestra estas frutas?',
        hint: 'Cuenta los mangos y los bananos, y busca la gráfica igual.',
        scene: pile,
        choices: graphs.map(([m, b]) => ({
          correct: m === mangos && b === bananos,
          draw: (ctx, box) => pictograph(ctx, box, [[mango, m], [banano, b]]),
        })),
      },
    ];
  }
}
