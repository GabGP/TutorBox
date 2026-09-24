// Nivel 7 · Quetzales y Centavos
// CNB Segundo, competencia 7 — 7.6.2 (lectura y escritura de cantidades de dinero), 7.6.1
// (réplicas de monedas y billetes del país), 7.6.3 (estimar el costo de bienes) y 7.6.4 (usar
// monedas y billetes en situaciones imaginarias). Los totales se suman en código.
import { ChoiceLesson, pickChoices, stacked } from '../shared/choice-lesson.js';
import { drawCoin, drawEmoji, drawText } from '../shared/draw.js';

const BILL_COLOR = { 5: '#8E24AA', 10: '#E53935', 20: '#1E88E5', 50: '#FB8C00', 100: '#6D4C41' };
const sum = (money) => money.reduce((a, b) => a + b, 0);
const quetzales = (ctx, value, box) => drawText(ctx, `Q${value}`, box);

function bill(ctx, cx, cy, w, value) {
  const h = w * 0.5;
  ctx.save();
  ctx.fillStyle = BILL_COLOR[value];
  ctx.strokeStyle = 'rgba(0,0,0,0.3)';
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.roundRect(cx - w / 2, cy - h / 2, w, h, 6); ctx.fill(); ctx.stroke();
  ctx.fillStyle = 'rgba(255,255,255,0.35)';
  ctx.beginPath(); ctx.ellipse(cx - w * 0.22, cy, h * 0.3, h * 0.35, 0, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
  drawText(ctx, `Q${value}`, { x: cx, y: cy - h / 2, w: w / 2, h }, '#FFFFFF');
}

function centavos(ctx, cx, cy, r, value) {
  ctx.fillStyle = '#CFD8DC';
  ctx.strokeStyle = '#78909C';
  ctx.lineWidth = Math.max(2, r * 0.12);
  ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
  drawText(ctx, `${value}c`, { x: cx - r, y: cy - r, w: r * 2, h: r * 2 }, '#37474F');
}

/** Bills and Q1 coins laid out in rows, as they would sit on a table. */
function table(ctx, box, money) {
  const cols = Math.min(money.length, 4);
  const rows = Math.ceil(money.length / cols);
  const w = box.w / cols;
  const h = box.h / rows;
  money.forEach((v, i) => {
    const cx = box.x + w * ((i % cols) + 0.5);
    const cy = box.y + h * (Math.floor(i / cols) + 0.5);
    if (v === 1) drawCoin(ctx, cx, cy, Math.min(w, h) * 0.32);
    else bill(ctx, cx, cy, Math.min(w * 0.9, h * 1.6), v);
  });
}

const PRICES = [['🚲', 800], ['🍬', 1], ['✏️', 2]];

export default class DineroLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a jugar a la tienda con quetzales!'; }
  get colors() { return ['#E1F5FE', '#E8F5E9']; }

  makeRounds() {
    const purse = [10, 5, 1, 1];
    const big = [20, 20, 10];
    const cost = 8;
    const groups = [[5, 1, 1], [5, 1, 1, 1], [10]]; // stacked, not shuffled: exact one in the middle
    const [paid, price] = [20, 12];
    const quarter = 25;
    const priciest = Math.max(...PRICES.map(([, p]) => p));
    return [
      {
        say: 'Ana tiene este dinero. ¿Cuántos quetzales tiene?',
        ask: '¿Cuánto dinero hay?',
        hint: 'Empieza por el billete más grande y sigue sumando.',
        scene: (ctx, box) => table(ctx, box, purse),
        choices: pickChoices(sum(purse), [purse.length, sum(purse) - 1], { draw: quetzales }),
      },
      {
        say: `El cuaderno cuesta ${cost} quetzales. ¿Con qué grupo pagas exacto, sin que te den vuelto?`,
        ask: `¿Qué grupo suma Q${cost}?`,
        hint: 'Suma el dinero de cada grupo.',
        choices: stacked(groups.map((g) => ({ value: sum(g), correct: sum(g) === cost, draw: (ctx, box) => table(ctx, box, g) }))),
      },
      {
        say: `Pagas con un billete de ${paid} quetzales una mochila de ${price}. ¿Cuánto te dan de vuelto?`,
        ask: `Pagas Q${paid}, cuesta Q${price}`,
        hint: `Resta: ${paid} menos ${price}. O cuenta desde ${price} hasta ${paid}.`,
        scene: (ctx, box) => {
          table(ctx, { ...box, w: box.w / 2 }, [paid]);
          drawEmoji(ctx, '🎒', box.x + box.w * 0.75, box.y + box.h * 0.4, box.h * 0.45);
          drawText(ctx, `Q${price}`, { x: box.x + box.w / 2, y: box.y + box.h * 0.68, w: box.w / 2, h: box.h * 0.25 });
        },
        choices: pickChoices(paid - price, [paid + price, price], { draw: quetzales }),
      },
      {
        say: `¿Cuántas monedas de ${quarter} centavos forman un quetzal?`,
        ask: `¿Cuántas de ${quarter} centavos hacen Q1?`,
        hint: `Un quetzal son 100 centavos. Cuenta de ${quarter} en ${quarter}: 25, 50, 75, 100.`,
        scene: (ctx, box) => {
          const r = Math.min(box.w, box.h) * 0.2;
          centavos(ctx, box.x + box.w * 0.25, box.y + box.h / 2, r, quarter);
          drawText(ctx, '→', { x: box.x + box.w * 0.4, y: box.y, w: box.w * 0.2, h: box.h });
          drawCoin(ctx, box.x + box.w * 0.75, box.y + box.h / 2, r);
        },
        choices: pickChoices(100 / quarter, [quarter, 2]),
      },
      {
        say: '¿Qué cuesta MÁS?',
        ask: '¿Qué cuesta más?',
        hint: 'Piensa cuántos quetzales pagarías por cada cosa en la tienda.',
        choices: PRICES.map(([item, p]) => ({
          correct: p === priciest,
          draw: (ctx, box) => drawEmoji(ctx, item, box.x + box.w / 2, box.y + box.h / 2, Math.min(box.w, box.h) * 0.7),
        })),
      },
      {
        say: 'Don Carlos tiene estos billetes. ¿Cuánto dinero es?',
        ask: '¿Cuánto dinero hay?',
        hint: 'Veinte más veinte, y después suma diez.',
        scene: (ctx, box) => table(ctx, box, big),
        choices: pickChoices(sum(big), [big.length, sum(big) - 10], { draw: quetzales }),
      },
    ];
  }
}
