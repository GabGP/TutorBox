// Nivel 4 · Dividir y lo que Sobra
// CNB Tercero, competencia 4 — 4.3.3 (divisiones con y sin residuo, dividendo de uno o dos dígitos
// y divisor de un dígito) y 4.3.5 (cálculo mental de divisiones). Distractor clave: un residuo
// mayor que el divisor (26 ÷ 4 = 5 y sobran 6).
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { drawItems } from '../shared/draw.js';
import { mango } from '../shared/art.js';

const divide = (a, b) => ({ q: Math.floor(a / b), r: a % b });
const label = ({ q, r }) => (r ? `${q} r ${r}` : `${q}`);

export default class DivisionResiduoLesson extends ChoiceLesson {
  get intro() { return '¡A veces, al repartir, sobra algo!'; }
  get colors() { return ['#FFFDE7', '#FBE9E7']; }

  makeRounds() {
    const [mangos, bag] = [17, 5];
    const full = divide(mangos, bag);
    const [sweets, kids] = [26, 4];
    const share = divide(sweets, kids);
    const [eggs, nine] = [36, 9];
    const [big, two] = [80, 2];
    const scene = (ctx, box) => drawItems(ctx, mango, mangos, box);
    return [
      {
        say: `Hay ${mangos} mangos y los ponemos en bolsas de ${bag}. ¿Cuántas bolsas se llenan completas?`,
        ask: `¿Cuántas bolsas de ${bag} se llenan?`,
        hint: `Cuenta de ${bag} en ${bag}: ${bag}, ${bag * 2}, ${bag * 3}... sin pasarte de ${mangos}.`,
        scene,
        choices: pickChoices(full.q, [full.q + 1, mangos - bag]),
      },
      {
        say: `Después de llenar las bolsas, ¿cuántos mangos sobran?`,
        ask: '¿Cuántos mangos sobran?',
        hint: `Llenaste ${full.q} bolsas de ${bag}: son ${full.q * bag} mangos. ¿Cuántos faltan para ${mangos}?`,
        scene,
        choices: pickChoices(full.r, [bag - full.r, bag]),
      },
      {
        say: `Reparte ${sweets} dulces entre ${kids} niños, todos igual. ¿Cuántos le tocan a cada uno y cuántos sobran?`,
        ask: `${sweets} ÷ ${kids} = ?`,
        hint: `La r quiere decir residuo: lo que sobra. Lo que sobra siempre es menor que ${kids}.`,
        scene: (ctx, box) => drawItems(ctx, '🍬', sweets, box),
        choices: pickChoices(label(share), [label({ q: share.q - 1, r: share.r + kids }), label({ q: share.q, r: 0 })]),
      },
      {
        say: `Hay ${eggs} huevos y se reparten entre ${nine} familias. ¿Cuántos le tocan a cada familia?`,
        ask: `${eggs} ÷ ${nine} = ?`,
        hint: `Piensa: ¿qué número por ${nine} da ${eggs}?`,
        choices: pickChoices(label(divide(eggs, nine)), [label({ q: eggs - nine, r: 0 }), label({ q: eggs / nine + 1, r: 0 })]),
      },
      {
        say: `Calcula en tu mente: ${big} dividido entre ${two}.`,
        ask: `${big} ÷ ${two} = ?`,
        hint: `La mitad de 8 decenas son 4 decenas.`,
        choices: pickChoices(label(divide(big, two)), [label({ q: big / two / 10, r: 0 }), label({ q: big * two, r: 0 })]),
      },
    ];
  }
}
