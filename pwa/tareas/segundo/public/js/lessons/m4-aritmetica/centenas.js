// Nivel 4 · Centenas, Decenas y Unidades
// CNB Segundo, competencia 4 — 4.4.1 (valor relativo y absoluto, 0 a 999), 4.3.1 (concepto de
// centena) y 4.3.2 (lectura y escritura de números hasta 1,000).
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { drawBlocks, drawText, inset } from '../shared/draw.js';

const digits = (n) => [Math.floor(n / 100), Math.floor(n / 10) % 10, n % 10];

// Wrong answers: tens and units swapped, or the zero left out / every piece counted as one.
function blocks(n) {
  const [h, t, u] = digits(n);
  return {
    say: 'Las placas grandes son centenas, las barras son decenas y los cubitos son unidades. ¿Qué número forman?',
    ask: '¿Qué número forman los bloques?',
    hint: `Cuenta: ${h} centenas, ${t} decenas y ${u} unidades.`,
    scene: (ctx, box) => drawBlocks(ctx, n, inset(box, 0.04)),
    choices: pickChoices(n, [h * 100 + u * 10 + t, t ? h + t + u : h * 10 + u]),
  };
}

// A number with one digit painted orange.
function numberWith(ctx, box, n, digit) {
  const s = String(n);
  const w = box.w / (s.length + 1);
  [...s].forEach((d, i) => {
    drawText(ctx, d, { x: box.x + w * (i + 0.5), y: box.y, w, h: box.h }, i === digit ? '#EF6C00' : '#1F2A1F');
  });
}

export default class CentenasLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a contar con centenas, decenas y unidades!'; }
  get colors() { return ['#FFFDE7', '#E3F2FD']; }

  makeRounds() {
    const tens = 10;
    const [n, place] = [472, 1];
    const value = digits(n)[place] * 10 ** (2 - place);
    return [
      blocks(235),
      {
        say: 'Aquí hay diez barras de diez. Juntas forman una placa de cien. ¿Cuántas decenas forman una centena?',
        ask: '¿Cuántas decenas forman una centena?',
        hint: 'Cuenta las barras azules.',
        scene: (ctx, box) => {
          for (let i = 0; i < tens; i++) drawBlocks(ctx, 10, { x: box.x + box.w * (0.04 + i * 0.045), y: box.y + box.h * 0.1, w: box.w * 0.04, h: box.h * 0.8 });
          drawText(ctx, '=', { x: box.x + box.w * 0.5, y: box.y, w: box.w * 0.1, h: box.h });
          drawBlocks(ctx, tens * 10, { x: box.x + box.w * 0.6, y: box.y + box.h * 0.1, w: box.w * 0.36, h: box.h * 0.8 });
        },
        choices: pickChoices(tens, [100, 1]),
      },
      blocks(106),
      {
        say: `En el número ${n}, ¿cuánto vale el 7?`,
        ask: `En ${n}, ¿cuánto vale el 7?`,
        hint: 'El 7 está en el lugar de las decenas. Siete decenas valen...',
        scene: (ctx, box) => numberWith(ctx, inset(box, 0.1, 0.2), n, place),
        choices: pickChoices(value, [value / 10, value * 10]),
      },
      {
        say: '¿Cuál es el número trescientos ocho?',
        ask: '¿Cuál es trescientos ocho?',
        hint: 'Trescientos son 3 centenas. No hay decenas, así que va un cero en medio.',
        choices: pickChoices(3 * 100 + 8, [38, 380]),
      },
      {
        say: 'Aquí hay diez centenas. Diez centenas forman mil. ¿Qué número es?',
        ask: '¿Qué número forman diez centenas?',
        hint: 'Cuenta de cien en cien: cien, doscientos, trescientos...',
        scene: (ctx, box) => {
          // Two rows of five hundreds, so each plate stays big enough to see.
          const half = { ...box, h: box.h / 2 };
          drawBlocks(ctx, 5 * 100, inset(half, 0.04, 0.06));
          drawBlocks(ctx, 5 * 100, inset({ ...half, y: box.y + box.h / 2 }, 0.04, 0.06));
        },
        choices: pickChoices(10 * 100, [100, 110]),
      },
    ];
  }
}
