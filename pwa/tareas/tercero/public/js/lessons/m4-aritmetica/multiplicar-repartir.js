// Nivel 4 · Multiplicar y Repartir
// CNB Tercero, competencia 4 — 4.3.1 (multiplicación de un dígito por dos o tres dígitos), 4.3.2
// (la división como reparto o agrupamiento) y 4.3.4 (relación inversa entre multiplicación y
// división). Distractores: sumar en vez de multiplicar, multiplicar solo las unidades y olvidar
// lo que se lleva.
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { drawBasket, drawItems, drawText } from '../shared/draw.js';
import { elote } from '../shared/art.js';
import { column } from './sumas-restas.js';

/** Multiplying only the units (23 × 3 -> 29). */
const onlyUnits = (n, k) => n - (n % 10) + (n % 10) * k;
/** Writing each column's full product without carrying (45 × 3 -> 125). */
const forgotCarry = (n, k) => Number(String(n).split('').map((d, i) => (i === 0 ? d * k : (d * k) % 10)).join(''));

function times(n, k, say) {
  const answer = n * k;
  return {
    say,
    ask: `${n} × ${k} = ?`,
    hint: `Multiplica las unidades por ${k}, luego las decenas. Si pasa de 9, lleva a la siguiente columna.`,
    scene: (ctx, box) => column(ctx, box, n, '×', k),
    choices: pickChoices(answer, [onlyUnits(n, k), forgotCarry(n, k), n + k].filter((v) => v !== answer).slice(0, 2)),
  };
}

export default class MultiplicarRepartirLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a multiplicar y a repartir en partes iguales!'; }
  get colors() { return ['#FFFDE7', '#FFF3E0']; }

  makeRounds() {
    const [corn, baskets] = [18, 3];
    const [eggs, carton] = [20, 5];
    const [a, b] = [7, 6];
    return [
      times(23, 3, 'En cada surco hay 23 matas de maíz. Hay 3 surcos. ¿Cuántas matas hay?'),
      times(124, 2, 'Un bus lleva 124 personas en cada viaje. Hizo 2 viajes. ¿Cuántas personas llevó?'),
      times(45, 3, 'Una caja tiene 45 lápices. ¿Cuántos lápices hay en 3 cajas?'),
      {
        say: `Reparte ${corn} elotes en ${baskets} canastas, todas con la misma cantidad. ¿Cuántos elotes van en cada canasta?`,
        ask: `${corn} ÷ ${baskets} = ?`,
        hint: `Pon un elote en cada canasta, una y otra vez, hasta repartir los ${corn}.`,
        scene: (ctx, box) => {
          drawItems(ctx, elote, corn, { x: box.x, y: box.y, w: box.w, h: box.h * 0.55 });
          for (let i = 0; i < baskets; i++) drawBasket(ctx, { x: box.x + box.w * (0.08 + i * 0.31), y: box.y + box.h * 0.62, w: box.w * 0.24, h: box.h * 0.34 });
        },
        choices: pickChoices(corn / baskets, [corn - baskets, corn * baskets]),
      },
      {
        say: `Hay ${eggs} huevos y en cada cartón caben ${carton}. ¿Cuántos cartones se llenan?`,
        ask: `¿Cuántos grupos de ${carton} hay en ${eggs}?`,
        hint: `Haz grupos de ${carton} huevos y cuenta los grupos.`,
        scene: (ctx, box) => drawItems(ctx, '🥚', eggs, box),
        choices: pickChoices(eggs / carton, [eggs - carton, eggs * carton]),
      },
      {
        say: `Si ${a} por ${b} es ${a * b}, ¿cuánto es ${a * b} dividido entre ${b}?`,
        ask: `${a} × ${b} = ${a * b}. ¿${a * b} ÷ ${b}?`,
        hint: 'La división deshace la multiplicación.',
        scene: (ctx, bx) => {
          drawText(ctx, `${a} × ${b} = ${a * b}`, { x: bx.x, y: bx.y + bx.h * 0.15, w: bx.w, h: bx.h * 0.3 });
          drawText(ctx, `${a * b} ÷ ${b} = ?`, { x: bx.x, y: bx.y + bx.h * 0.55, w: bx.w, h: bx.h * 0.3 }, '#EF6C00');
        },
        choices: pickChoices(a * b / b, [a * b - b, a * b + b]),
      },
    ];
  }
}
