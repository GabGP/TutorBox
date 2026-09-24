// Nivel 5 · Problemas del Mercado
// CNB Segundo, competencia 5 — 5.1.1 (problemas con una o dos operaciones), 5.1.2 (elegir la
// operación) y 5.2.2 (problemas con moneda). Distractor principal: usar la operación equivocada o
// hacer solo la primera de dos operaciones.
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { drawEmoji, drawText } from '../shared/draw.js';
import { aguacate, elote, gallina, mango, naranja } from '../shared/art.js';

// Each thing in the story: its picture with its number underneath.
function story(ctx, box, parts) {
  const w = box.w / parts.length;
  parts.forEach(([art, label], i) => {
    const cx = box.x + w * (i + 0.5);
    drawEmoji(ctx, art, cx, box.y + box.h * 0.38, Math.min(w, box.h) * 0.55);
    drawText(ctx, label, { x: box.x + w * i, y: box.y + box.h * 0.7, w, h: box.h * 0.25 });
  });
}

const quetzales = (ctx, value, box) => drawText(ctx, `Q${value}`, box);

export default class ProblemasMercadoLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a resolver problemas en el mercado!'; }
  get colors() { return ['#EFEBE9', '#FFF8E1']; }

  makeRounds() {
    const [had, bought] = [25, 13];
    const [stock, sold] = [48, 15];
    const [morning, afternoon, gone] = [20, 15, 10];
    const [hens, eggs] = [4, 2];
    const [price, many] = [3, 3];
    return [
      {
        say: `María tenía ${had} mangos. Compró ${bought} más. ¿Cuántos mangos tiene ahora?`,
        ask: `${had} mangos, compró ${bought} más`,
        hint: 'Si compra más, tiene más. Hay que sumar.',
        scene: (ctx, b) => story(ctx, b, [[mango, had], ['🛒', `+ ${bought}`]]),
        choices: pickChoices(had + bought, [had - bought, had + bought - 1]),
      },
      {
        say: `En el puesto hay ${stock} naranjas. Se vendieron ${sold}. ¿Cuántas quedan?`,
        ask: `${stock} naranjas, se vendieron ${sold}`,
        hint: 'Si se venden, quedan menos. Hay que restar.',
        scene: (ctx, b) => story(ctx, b, [[naranja, stock], ['🛍️', `− ${sold}`]]),
        choices: pickChoices(stock - sold, [stock + sold, stock - sold + 1]),
      },
      {
        say: `Don Juan cosechó ${morning} elotes en la mañana y ${afternoon} en la tarde. Vendió ${gone}. ¿Cuántos elotes le quedan?`,
        ask: `${morning} + ${afternoon} elotes, vendió ${gone}`,
        hint: 'Son dos pasos: primero junta los elotes de la mañana y de la tarde, después quita los vendidos.',
        scene: (ctx, b) => story(ctx, b, [['🌅', morning], ['🌇', afternoon], [elote, `− ${gone}`]]),
        choices: pickChoices(morning + afternoon - gone, [morning + afternoon, morning + afternoon + gone]),
      },
      {
        say: `Cada gallina puso ${eggs} huevos. Hay ${hens} gallinas. ¿Cuántos huevos hay en total?`,
        ask: `${hens} gallinas, ${eggs} huevos cada una`,
        hint: `Cuenta ${eggs} huevos por cada gallina.`,
        scene: (ctx, b) => story(ctx, b, [[gallina, hens], ['🥚', `${eggs} c/u`]]),
        choices: pickChoices(hens * eggs, [hens + eggs, hens * eggs + eggs]),
      },
      {
        say: `Un aguacate cuesta ${price} quetzales. ¿Cuánto pagas por ${many} aguacates?`,
        ask: `${many} aguacates a Q${price} cada uno`,
        hint: `Paga ${price} quetzales por cada aguacate.`,
        scene: (ctx, b) => story(ctx, b, [[aguacate, `× ${many}`], ['🏷️', `Q${price}`]]),
        choices: pickChoices(price * many, [price + many, price * many + price], { draw: quetzales }),
      },
    ];
  }
}
