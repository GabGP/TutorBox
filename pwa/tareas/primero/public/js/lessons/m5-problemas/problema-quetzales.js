// Módulo 5 · Quetzales del Mercado
// CNB Primero 7.4.1 (monedas del país en compra y venta) y 5.3.1 (problemas con suma o resta).
import { ChoiceLesson, numberChoices } from '../shared/choice-lesson.js';
import { drawCoins, drawEmoji } from '../shared/draw.js';

// Every coin card uses the grid of the biggest one, so all coins are the same size.
const coins = (answer) => numberChoices(answer, { min: 1, max: 8, draw: (ctx, n, box) => drawCoins(ctx, n, box, answer + 2) });

function priceTag(ctx, cx, cy, price, size) {
  const w = size * 0.9;
  const h = size * 0.42;
  ctx.fillStyle = '#FFFFFF';
  ctx.strokeStyle = '#9C7A1F';
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.roundRect(cx - w / 2, cy - h / 2, w, h, 8); ctx.fill(); ctx.stroke();
  ctx.fillStyle = '#1F2A1F';
  ctx.font = `900 ${Math.round(h * 0.7)}px Nunito, sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(`Q${price}`, cx, cy + 1);
}

// Items for sale: [emoji, price]. The scene lays them out side by side with their tags.
function stall(ctx, box, items) {
  const cell = box.w / items.length;
  const size = Math.min(cell * 0.6, box.h * 0.5);
  items.forEach(([emoji, price], i) => {
    const cx = box.x + cell * (i + 0.5);
    drawEmoji(ctx, emoji, cx, box.y + box.h * 0.38, size);
    if (price) priceTag(ctx, cx, box.y + box.h * 0.8, price, size);
  });
}

export default class ProblemaQuetzalesLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a comprar al mercado con quetzales!'; }
  get colors() { return ['#FFF3E0', '#FFECB3']; }

  makeRounds() {
    const [elote, aguacate] = [2, 2];
    const [tengo, pina] = [6, 4];
    return [
      {
        say: 'Un mango cuesta 3 quetzales. ¿Con cuántas monedas de un quetzal lo pagas?',
        ask: 'Mango: Q3. ¿Cuántas monedas?',
        hint: 'Una moneda por cada quetzal. Cuenta las monedas.',
        scene: (ctx, box) => stall(ctx, box, [['🥭', 3]]),
        choices: coins(3),
      },
      {
        say: `Compras un elote de ${elote} quetzales y un aguacate de ${aguacate} quetzales. ¿Cuántas monedas pagas en total?`,
        ask: `Q${elote} + Q${aguacate} = ?`,
        hint: 'Junta las monedas del elote y las del aguacate.',
        scene: (ctx, box) => stall(ctx, box, [['🌽', elote], ['🥑', aguacate]]),
        choices: coins(elote + aguacate),
      },
      {
        say: `Tienes ${tengo} quetzales. Compras una piña de ${pina} quetzales. ¿Cuántos quetzales te quedan?`,
        ask: `Q${tengo} − Q${pina} = ?`,
        hint: `Quita ${pina} monedas y cuenta las que quedan.`,
        scene: (ctx, box) => {
          drawCoins(ctx, tengo, { x: box.x, y: box.y + box.h * 0.1, w: box.w * 0.55, h: box.h * 0.8 });
          stall(ctx, { x: box.x + box.w * 0.55, y: box.y, w: box.w * 0.45, h: box.h }, [['🍍', pina]]);
        },
        choices: coins(tengo - pina),
      },
      {
        say: '¿Qué cuesta MÁS: el tomate, la sandía o el banano?',
        ask: '¿Qué cuesta más?',
        hint: 'Mira el número de cada precio. El más grande cuesta más.',
        choices: [['🍅', 1], ['🍉', 5], ['🍌', 2]].map(([emoji, price], _, all) => ({
          correct: price === Math.max(...all.map(([, p]) => p)),
          draw: (ctx, box) => stall(ctx, box, [[emoji, price]]),
        })),
      },
    ];
  }
}
