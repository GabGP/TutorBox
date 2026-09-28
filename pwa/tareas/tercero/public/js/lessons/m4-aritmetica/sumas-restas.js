// Nivel 4 · Sumas y Restas Grandes
// CNB Tercero, competencia 4 — 4.2.1 y 4.2.3 (sumas y restas hasta 4 dígitos), 4.2.2 (propiedad
// conmutativa), 4.2.4 (relación inversa entre suma y resta) y 4.2.5 (cálculo mental).
// Distractores del algoritmo: olvidar lo que se lleva y restar el dígito menor del mayor.
import { ChoiceLesson, pickChoices, stacked } from '../shared/choice-lesson.js';
import { drawText, num } from '../shared/draw.js';

const columns = (n, len) => String(n).padStart(len, '0').split('').map(Number);
const fromColumns = (d) => d.reduce((a, x) => a * 10 + x, 0);
const width = (a, b) => Math.max(String(a).length, String(b).length);

/** Adding each column without carrying (1,568 + 2,275 -> 3,733). */
export function noCarry(a, b) {
  const [x, y] = [columns(a, width(a, b)), columns(b, width(a, b))];
  return fromColumns(x.map((d, i) => (d + y[i]) % 10));
}

/** Subtracting the smaller digit from the bigger one in each column (5,000 - 1,234 -> 4,234). */
export function smallFromBig(a, b) {
  const [x, y] = [columns(a, width(a, b)), columns(b, width(a, b))];
  return fromColumns(x.map((d, i) => Math.abs(d - y[i])));
}

/** The operation written the school way: right-aligned numbers, the sign and a line. */
export function column(ctx, box, a, sign, b) {
  const rows = [num(a), `${sign} ${num(b)}`];
  const size = Math.min(box.h * 0.2, box.w * 0.12);
  const right = box.x + box.w * 0.72;
  const y1 = box.y + box.h * 0.25;
  const y2 = y1 + size * 1.3;
  ctx.save();
  ctx.fillStyle = '#1F2A1F';
  ctx.font = `900 ${Math.round(size)}px Nunito, sans-serif`;
  ctx.textAlign = 'right';
  ctx.textBaseline = 'middle';
  ctx.fillText(rows[0], right, y1);
  ctx.fillText(rows[1], right, y2);
  const w = Math.max(ctx.measureText(rows[0]).width, ctx.measureText(rows[1]).width);
  ctx.fillRect(right - w - 6, y2 + size * 0.7, w + 12, 4);
  ctx.fillStyle = '#EF6C00';
  ctx.fillText('?', right, y2 + size * 1.5);
  ctx.restore();
}

function op(a, sign, b, say, hint, wrongs) {
  const answer = sign === '+' ? a + b : a - b;
  return {
    say,
    ask: `${num(a)} ${sign} ${num(b)} = ?`,
    hint,
    scene: (ctx, box) => column(ctx, box, a, sign, b),
    choices: pickChoices(answer, wrongs(answer)),
  };
}

const evaluate = ([a, sign, b]) => (sign === '+' ? a + b : a - b);
const show = ([a, sign, b]) => `${num(a)} ${sign} ${num(b)}`;

export default class SumasRestasLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a sumar y restar números de miles!'; }
  get colors() { return ['#FFFDE7', '#F1F8E9']; }

  makeRounds() {
    const [x, y] = [350, 150];
    const target = [238, '+', 45];
    // Stacked cards are not shuffled: the right one sits in the middle.
    const options = [[238, '−', 45], [45, '+', 238], [238, '+', 54]];
    return [
      op(1568, '+', 2275, 'En la cooperativa vendieron 1,568 libras de café en marzo y 2,275 en abril. ¿Cuántas libras vendieron en total?',
        'Suma columna por columna desde las unidades. Cuando pasas de 9, llevas 1 a la siguiente columna.',
        (ans) => [noCarry(1568, 2275), ans + 100]),
      op(5000, '−', 1234, 'La escuela juntó 5,000 quetzales y gastó 1,234 en libros. ¿Cuánto le queda?',
        'Arriba hay ceros: presta de las unidades de millar, que se vuelven 4, y los ceros se vuelven nueves.',
        (ans) => [smallFromBig(5000, 1234), ans + 1000]),
      op(4352, '−', 1128, 'Había 4,352 mazorcas y se usaron 1,128. ¿Cuántas quedan?',
        'A 2 no le puedes quitar 8: presta una decena. Las 5 decenas se vuelven 4.',
        (ans) => [smallFromBig(4352, 1128), ans + 10]),
      {
        say: `Si ${x} más ${y} es ${x + y}, ¿cuánto es ${x + y} menos ${y}?`,
        ask: `${x} + ${y} = ${x + y}. ¿${x + y} − ${y}?`,
        hint: 'La resta deshace la suma: si quitas lo que sumaste, vuelves al principio.',
        scene: (ctx, box) => {
          drawText(ctx, `${x} + ${y} = ${x + y}`, { x: box.x, y: box.y + box.h * 0.15, w: box.w, h: box.h * 0.3 });
          drawText(ctx, `${x + y} − ${y} = ?`, { x: box.x, y: box.y + box.h * 0.55, w: box.w, h: box.h * 0.3 }, '#EF6C00');
        },
        choices: pickChoices(x + y - y, [x + y + y, y]),
      },
      {
        say: `¿Cuál de estas sumas da lo mismo que ${show(target)}?`,
        ask: `¿Cuál da lo mismo que ${show(target)}?`,
        hint: 'Si cambias el orden de los números en una suma, el resultado no cambia.',
        choices: stacked(options.map((o) => ({ value: show(o), correct: evaluate(o) === evaluate(target), draw: (ctx, box) => drawText(ctx, show(o), box) }))),
      },
      op(2500, '+', 1500, 'Calcula en tu mente: 2,500 más 1,500.',
        'Primero los miles: 2,000 más 1,000. Después 500 más 500 son otros mil.',
        (ans) => [noCarry(2500, 1500), ans + 500]),
    ];
  }
}
