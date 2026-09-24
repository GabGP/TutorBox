// Nivel 4 · Números Mayas
// CNB Segundo, competencia 4 — 4.1.3 (lectura y escritura de numerales mayas 0-400), 4.1.1
// (agrupamiento de veintenas), 4.1.2 (el cero) y 4.7.4 (suma con numeración maya, hasta 19).
// Los distractores son lecturas equivocadas reales: la barra leída como 10, o la veintena de
// arriba leída como unidad.
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { drawMaya, drawNumeral, drawText, inset } from '../shared/draw.js';

function read(n, say, hint) {
  const [hi, lo] = [Math.floor(n / 20), n % 20];
  const [bars, dots] = [Math.floor(lo / 5), lo % 5];
  const wrongs = hi ? [hi + lo, hi * 10 + lo] : [bars * 10 + dots, bars + dots];
  return {
    say,
    ask: '¿Qué número maya es este?',
    hint,
    scene: (ctx, box) => drawMaya(ctx, n, inset(box, 0.12, 0.06)),
    choices: pickChoices(n, wrongs, { draw: drawNumeral }),
  };
}

export default class NumerosMayasLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a leer números como los antiguos mayas!'; }
  get colors() { return ['#FFFDE7', '#EFEBE9']; }

  makeRounds() {
    const [a, b] = [7, 6];
    return [
      read(8, 'Un punto vale uno y una barra vale cinco. ¿Qué número es?', 'La barra vale 5. Después cuenta los puntos: 6, 7, 8...'),
      read(14, 'Mira las barras y los puntos. ¿Qué número es?', 'Cada barra vale 5: 5, 10. Después suma los puntos.'),
      {
        say: 'Los mayas inventaron el cero hace mucho tiempo. ¿Cuál es el cero maya?',
        ask: '¿Cuál es el cero maya?',
        hint: 'El cero maya parece una concha, un caracol.',
        choices: pickChoices(0, [1, 5], { draw: drawMaya }),
      },
      read(20, 'Este número tiene dos pisos. El piso de arriba cuenta veintenas. ¿Qué número es?', 'Arriba hay un punto: una veintena, o sea 20. Abajo hay cero.'),
      read(47, 'Otro número de dos pisos. Arriba cuenta veintenas y abajo unidades. ¿Qué número es?', 'Arriba: 2 veintenas son 40. Abajo: una barra y dos puntos son 7.'),
      {
        say: `Vamos a sumar con números mayas: ${a} más ${b}. ¿Cuál es el resultado?`,
        ask: `${a} + ${b} = ?`,
        hint: 'Junta todos los puntos y barras. Cada cinco puntos se vuelven una barra.',
        scene: (ctx, box) => {
          const w = box.w / 3;
          drawMaya(ctx, a, inset({ ...box, w }, 0.18, 0.15));
          drawText(ctx, '+', { x: box.x + w, y: box.y, w, h: box.h });
          drawMaya(ctx, b, inset({ ...box, x: box.x + 2 * w, w }, 0.18, 0.15));
        },
        choices: pickChoices(a + b, [a + b - 1, a + b + 1], { draw: drawMaya }),
      },
    ];
  }
}
