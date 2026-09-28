// Nivel 7 · Quetzales y Centavos
// CNB Tercero, competencia 7 — 7.5.2 (escribir cantidades de dinero con el símbolo Q y el punto
// decimal), 7.5.1 (equivalencias entre monedas y billetes) y 7.5.3 (compra y venta en el
// mercado). Todo se cuenta en centavos para que las cuentas sean exactas.
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { drawCoin, drawEmoji, drawText, num } from '../shared/draw.js';

const PER_QUETZAL = 100;
const BILL_COLOR = { 5: '#8E24AA', 10: '#E53935', 20: '#1E88E5', 50: '#FB8C00', 100: '#6D4C41' };
/** Centavos written the Guatemalan way: 1575 -> "Q15.75". */
const q = (cents) => `Q${num(Math.floor(cents / PER_QUETZAL))}.${String(cents % PER_QUETZAL).padStart(2, '0')}`;
const sum = (list) => list.reduce((a, b) => a + b, 0);
/** Centavos said aloud: 850 -> "8 quetzales con 50 centavos" (Q8.50 would be read letter by letter). */
const spoken = (cents) => `${Math.floor(cents / PER_QUETZAL)} quetzales con ${cents % PER_QUETZAL} centavos`;

function bill(ctx, cx, cy, w, quetzales) {
  const h = w * 0.5;
  ctx.save();
  ctx.fillStyle = BILL_COLOR[quetzales];
  ctx.strokeStyle = 'rgba(0,0,0,0.3)';
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.roundRect(cx - w / 2, cy - h / 2, w, h, 6); ctx.fill(); ctx.stroke();
  ctx.fillStyle = 'rgba(255,255,255,0.35)';
  ctx.beginPath(); ctx.ellipse(cx - w * 0.22, cy, h * 0.3, h * 0.35, 0, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
  drawText(ctx, `Q${quetzales}`, { x: cx, y: cy - h / 2, w: w / 2, h }, '#FFFFFF');
}

function centavos(ctx, cx, cy, r, value) {
  ctx.fillStyle = '#CFD8DC';
  ctx.strokeStyle = '#78909C';
  ctx.lineWidth = Math.max(2, r * 0.12);
  ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
  drawText(ctx, `${value}c`, { x: cx - r, y: cy - r, w: r * 2, h: r * 2 }, '#37474F');
}

/** Money on a table; each item is in centavos (bills from Q5, a Q1 coin, smaller coins). */
function table(ctx, box, money) {
  const cols = Math.min(money.length, 4);
  const rows = Math.ceil(money.length / cols);
  const [w, h] = [box.w / cols, box.h / rows];
  money.forEach((c, i) => {
    const cx = box.x + w * ((i % cols) + 0.5);
    const cy = box.y + h * (Math.floor(i / cols) + 0.5);
    if (c >= 5 * PER_QUETZAL) bill(ctx, cx, cy, Math.min(w * 0.92, h * 1.6), c / PER_QUETZAL);
    else if (c === PER_QUETZAL) drawCoin(ctx, cx, cy, Math.min(w, h) * 0.3);
    else centavos(ctx, cx, cy, Math.min(w, h) * 0.3, c);
  });
}

function priced(item, cents) {
  return (ctx, box) => {
    drawEmoji(ctx, item, box.x + box.w / 2, box.y + box.h * 0.38, Math.min(box.w, box.h) * 0.5);
    drawText(ctx, q(cents), { x: box.x, y: box.y + box.h * 0.72, w: box.w, h: box.h * 0.22 });
  };
}

export default class QuetzalesLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a jugar al mercado con quetzales y centavos!'; }
  get colors() { return ['#E1F5FE', '#E8F5E9']; }

  makeRounds() {
    const purse = [1000, 500, 50, 25];
    const coinsAsQuetzales = sum(purse.map((c) => (c < PER_QUETZAL ? c * PER_QUETZAL : c)));
    const ten = 10;
    const written = 12 * PER_QUETZAL + 50;
    const [paid, price] = [10 * PER_QUETZAL, 850];
    const [tomato, tomatoes] = [75, 4];
    const wallet = 20 * PER_QUETZAL;
    const shop = [['⚽', 1800], ['🎒', 8500], ['👟', 12000]];
    return [
      {
        say: 'Ana tiene estos billetes y monedas. ¿Cuánto dinero tiene?',
        ask: '¿Cuánto dinero hay?',
        hint: 'Suma primero los billetes. Después los centavos: 50 y 25.',
        scene: (ctx, box) => table(ctx, box, purse),
        choices: pickChoices(q(sum(purse)), [q(coinsAsQuetzales), q(sum(purse.filter((c) => c >= PER_QUETZAL)))]),
      },
      {
        say: `Un quetzal son ${PER_QUETZAL} centavos. ¿Cuántas monedas de ${ten} centavos forman un quetzal?`,
        ask: `¿Cuántas de ${ten} centavos hacen Q1?`,
        hint: `Cuenta de ${ten} en ${ten} hasta llegar a ${PER_QUETZAL}.`,
        scene: (ctx, box) => {
          const r = Math.min(box.w, box.h) * 0.2;
          centavos(ctx, box.x + box.w * 0.25, box.y + box.h / 2, r, ten);
          drawText(ctx, '→', { x: box.x + box.w * 0.4, y: box.y, w: box.w * 0.2, h: box.h });
          drawCoin(ctx, box.x + box.w * 0.75, box.y + box.h / 2, r);
        },
        choices: pickChoices(PER_QUETZAL / ten, [PER_QUETZAL, ten / 2]),
      },
      {
        say: '¿Cómo se escribe doce quetzales con cincuenta centavos?',
        ask: 'Doce quetzales con 50 centavos',
        hint: 'Primero la Q, después los quetzales, un punto, y los centavos.',
        choices: pickChoices(q(written), [`Q${written}`, 'Q12.05']),
      },
      {
        say: `Compras un cuaderno de ${spoken(price)} y pagas con un billete de diez quetzales. ¿Cuánto te dan de vuelto?`,
        ask: `Pagas ${q(paid)}, cuesta ${q(price)}`,
        hint: `De ${q(price)} a Q9.00 faltan 50 centavos, y de Q9.00 a Q10.00, un quetzal.`,
        scene: (ctx, box) => {
          table(ctx, { ...box, w: box.w / 2 }, [paid]);
          priced('📓', price)(ctx, { ...box, x: box.x + box.w / 2, w: box.w / 2 });
        },
        choices: pickChoices(q(paid - price), [q(paid - price + PER_QUETZAL), q(paid + price)]),
      },
      {
        say: `En el mercado, un tomate cuesta ${tomato} centavos. ¿Cuánto cuestan ${tomatoes} tomates?`,
        ask: `${tomatoes} tomates a ${tomato} centavos`,
        hint: `Suma ${tomato} centavos ${tomatoes} veces. Cada ${PER_QUETZAL} centavos son un quetzal.`,
        choices: pickChoices(q(tomato * tomatoes), [q(tomato + tomatoes * PER_QUETZAL), q(tomato * tomatoes * 10)]),
      },
      {
        say: 'Tienes veinte quetzales. ¿Qué puedes comprar sin que te falte dinero?',
        ask: `Tienes ${q(wallet)}: ¿qué alcanza?`,
        hint: `Busca lo que cuesta menos de ${q(wallet)}.`,
        choices: shop.map(([item, cents]) => ({ value: cents, correct: cents <= wallet, draw: priced(item, cents) })),
      },
    ];
  }
}
