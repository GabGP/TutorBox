// Nivel 5 · Problemas de Dos Pasos
// CNB Tercero, competencia 5 — 5.2.1 (solución de problemas aplicando una o dos operaciones).
// Distractores: hacer solo el primer paso, o sumar todos los números del problema.
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { drawEmoji, drawText, num } from '../shared/draw.js';
import { elote, naranja } from '../shared/art.js';

// Each part of the story: its picture with its number underneath.
function story(ctx, box, parts) {
  const w = box.w / parts.length;
  parts.forEach(([art, label], i) => {
    drawEmoji(ctx, art, box.x + w * (i + 0.5), box.y + box.h * 0.38, Math.min(w, box.h) * 0.5);
    drawText(ctx, label, { x: box.x + w * i, y: box.y + box.h * 0.7, w, h: box.h * 0.22 });
  });
}

const quetzales = (ctx, v, box) => drawText(ctx, `Q${num(v)}`, box);

export default class ProblemasDosPasosLesson extends ChoiceLesson {
  get intro() { return '¡Estos problemas se resuelven en dos pasos!'; }
  get colors() { return ['#EFEBE9', '#FFF8E1']; }

  makeRounds() {
    const [sacks, price, fare] = [3, 125, 80];
    const [grades, each, absent] = [4, 28, 9];
    const [saved, stove, earned] = [1250, 875, 300];
    const [oranges, families, gift] = [48, 6, 2];
    const [riders, off, on] = [45, 12, 8];
    return [
      {
        say: `Don Luis vendió ${sacks} costales de maíz a ${price} quetzales cada uno. Pagó ${fare} quetzales de transporte. ¿Cuánto dinero le quedó?`,
        ask: `${sacks} × Q${price}, menos Q${fare}`,
        hint: 'Primer paso: cuánto ganó con los costales. Segundo paso: quítale el transporte.',
        scene: (ctx, box) => story(ctx, box, [[elote, `${sacks} × Q${price}`], ['🚚', `− Q${fare}`]]),
        choices: pickChoices(sacks * price - fare, [sacks * price, sacks * price + fare], { draw: quetzales }),
      },
      {
        say: `En la escuela hay ${grades} grados con ${each} alumnos cada uno. Hoy faltaron ${absent}. ¿Cuántos alumnos vinieron?`,
        ask: `${grades} × ${each}, faltaron ${absent}`,
        hint: 'Primero cuenta todos los alumnos. Después quita los que faltaron.',
        scene: (ctx, box) => story(ctx, box, [['🏫', `${grades} × ${each}`], ['🤒', `− ${absent}`]]),
        choices: pickChoices(grades * each - absent, [grades * each, grades * each + absent]),
      },
      {
        say: `María tenía ${num(saved)} quetzales. Compró una estufa de ${stove} y después ganó ${earned}. ¿Cuánto dinero tiene ahora?`,
        ask: `Q${num(saved)} − Q${stove} + Q${earned}`,
        hint: 'Primero resta lo que gastó. Después suma lo que ganó.',
        scene: (ctx, box) => story(ctx, box, [['🐷', `Q${num(saved)}`], ['🛒', `− Q${stove}`], ['💵', `+ Q${earned}`]]),
        choices: pickChoices(saved - stove + earned, [saved - stove, saved + stove + earned], { draw: quetzales }),
      },
      {
        say: `Hay ${oranges} naranjas para repartir igual entre ${families} familias. Cada familia regala ${gift}. ¿Cuántas naranjas le quedan a cada familia?`,
        ask: `${oranges} ÷ ${families}, menos ${gift}`,
        hint: 'Primero reparte entre las familias. Después quita las que regala cada una.',
        scene: (ctx, box) => story(ctx, box, [[naranja, oranges], ['🏠', `÷ ${families}`], ['🎁', `− ${gift}`]]),
        choices: pickChoices(oranges / families - gift, [oranges / families, oranges - families - gift]),
      },
      {
        say: `Un bus lleva ${riders} pasajeros. En la parada bajan ${off} y suben ${on}. ¿Cuántos pasajeros lleva ahora?`,
        ask: `${riders} − ${off} + ${on}`,
        hint: 'Los que bajan se restan y los que suben se suman.',
        scene: (ctx, box) => story(ctx, box, [['🚌', riders], ['⬇️', `− ${off}`], ['⬆️', `+ ${on}`]]),
        choices: pickChoices(riders - off + on, [riders - off, riders + off + on]),
      },
    ];
  }
}
