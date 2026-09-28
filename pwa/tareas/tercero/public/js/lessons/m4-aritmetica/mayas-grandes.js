// Nivel 4 · Números Mayas Grandes
// CNB Tercero, competencia 4 — 4.1.7 (numerales mayas de 0 a 7,999), 4.1.9 (antecesor y sucesor
// con numerales mayas), 4.2.6 (suma maya hasta 400) y 4.2.7 (resta maya hasta 400 sin
// transformación). Cada piso vale 20 veces el de abajo: unidades, veintenas y cuatrocientos.
// Distractores: sumar los pisos como si todos fueran unidades, o leerlos como centenas y decenas.
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { drawMaya, drawText, inset } from '../shared/draw.js';

const floors = (n) => {
  const d = [];
  do { d.unshift(n % 20); n = Math.floor(n / 20); } while (n > 0);
  return d;
};
const asDecimal = (d) => d.reduce((acc, x) => acc * 10 + x, 0);
const digitSum = (d) => d.reduce((a, b) => a + b, 0);

function read(n, say, hint) {
  const d = floors(n);
  return {
    say,
    ask: '¿Qué número maya es este?',
    hint,
    scene: (ctx, box) => drawMaya(ctx, n, inset(box, 0.22, 0.04)),
    choices: pickChoices(n, [digitSum(d), asDecimal(d)]),
  };
}

function operation(a, sign, b, say) {
  const answer = sign === '+' ? a + b : a - b;
  return {
    say,
    ask: sign === '+' ? 'Suma los números mayas' : 'Resta los números mayas',
    hint: 'Trabaja piso por piso: unidades con unidades y veintenas con veintenas.',
    scene: (ctx, box) => {
      const w = box.w / 3;
      drawMaya(ctx, a, inset({ ...box, w }, 0.15, 0.1));
      drawText(ctx, sign === '+' ? '+' : '−', { x: box.x + w, y: box.y, w, h: box.h });
      drawMaya(ctx, b, inset({ ...box, x: box.x + 2 * w, w }, 0.15, 0.1));
    },
    choices: pickChoices(answer, [sign === '+' ? answer - 20 : a + b, sign === '+' ? answer + 1 : answer - 20], { draw: drawMaya }),
  };
}

export default class MayasGrandesLesson extends ChoiceLesson {
  get intro() { return '¡Los números mayas también tienen pisos para los números grandes!'; }
  get colors() { return ['#FFFDE7', '#EFEBE9']; }

  makeRounds() {
    const [n1, n2, n3] = [125, 400, 1000];
    const [d1, d3] = [floors(n1), floors(n3)];
    return [
      read(n1, 'El piso de abajo cuenta unidades y el de arriba cuenta veintenas. ¿Qué número es?',
        `Arriba hay ${d1[0]} veintenas: ${d1[0]} por 20 son ${d1[0] * 20}. Abajo hay ${d1[1]}.`),
      read(n2, 'Este número tiene tres pisos. El tercer piso cuenta de 400 en 400. ¿Qué número es?',
        'Arriba hay un punto en el piso de 400. Los otros pisos tienen cero.'),
      read(n3, 'Otro número de tres pisos. ¿Qué número es?',
        `Arriba: ${d3[0]} por 400 son ${d3[0] * 400}. En medio: ${d3[1]} por 20 son ${d3[1] * 20}. Abajo: ${d3[2]}.`),
      {
        say: 'Este es el 400 en números mayas. ¿Cuál es el número que viene justo antes?',
        ask: '¿Qué número va justo antes?',
        hint: 'Antes de 400 viene 399: 19 veintenas y 19 unidades.',
        scene: (ctx, box) => drawMaya(ctx, n2, inset(box, 0.22, 0.04)),
        choices: pickChoices(n2 - 1, [n2 + 1, n2 - 20], { draw: drawMaya }),
      },
      operation(145, '+', 230, 'Suma estos dos números mayas. ¿Cuál es el resultado?'),
      operation(367, '−', 125, 'Ahora resta el segundo número maya del primero. ¿Cuál es el resultado?'),
    ];
  }
}
