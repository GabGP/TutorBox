// Nivel 1 · Piensa en el Patrón
// CNB Tercero, competencia 1 — 1.5.1 (construcción de patrones con objetos o figuras), 1.1.1
// (seguimiento de instrucciones en juegos con patrones) y 1.4.1 (por qué ocurre un patrón y sus
// consecuencias). Todas las respuestas salen de la regla del patrón.
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { drawShape, drawText } from '../shared/draw.js';

const RED = '#E53935';
const BLUE = '#1E88E5';
const YELLOW = '#FDD835';
const P = (kind, color) => ({ kind, color });
const same = (a, b) => a.kind === b.kind && a.color === b.color;
const COLOR_WORD = { [RED]: 'roja', [BLUE]: 'azul', [YELLOW]: 'amarilla' };

const piece = (p, scale = 0.38) => (ctx, box) => {
  drawShape(ctx, p.kind, box.x + box.w / 2, box.y + box.h / 2, Math.min(box.w, box.h) * scale, p.color);
};

// A woven band with one blinking gap anywhere in it.
function band(ctx, box, seq, gap, t) {
  const top = box.y + box.h * 0.25;
  const h = box.h * 0.5;
  ctx.fillStyle = '#6A1B9A';
  ctx.beginPath(); ctx.roundRect(box.x, top, box.w, h, 12); ctx.fill();
  const cell = box.w / seq.length;
  seq.forEach((p, i) => {
    const b = { x: box.x + cell * i, y: top + 8, w: cell, h: h - 16 };
    if (i !== gap) { piece(p)(ctx, b); return; }
    ctx.save();
    ctx.setLineDash([6, 5]);
    ctx.strokeStyle = `rgba(255,255,255,${0.6 + Math.sin(t * 4) * 0.4})`;
    ctx.lineWidth = 3;
    ctx.beginPath(); ctx.roundRect(b.x + 3, b.y + 3, b.w - 6, b.h - 6, 8); ctx.stroke();
    ctx.restore();
  });
}

// A necklace: beads 1..shown, then the numbered bead to guess.
function necklace(ctx, box, unit, shown, asked) {
  const n = shown + 2;
  const w = box.w / n;
  const y = box.y + box.h * 0.45;
  const r = Math.min(w * 0.38, box.h * 0.16);
  ctx.strokeStyle = '#8D6E63';
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(box.x, y); ctx.lineTo(box.x + box.w, y); ctx.stroke();
  for (let i = 0; i < n; i++) {
    const cx = box.x + w * (i + 0.5);
    const label = i < shown ? i + 1 : i === shown ? '…' : asked;
    if (i < shown) {
      ctx.fillStyle = unit[i % unit.length];
      ctx.beginPath(); ctx.arc(cx, y, r, 0, Math.PI * 2); ctx.fill();
    } else if (i > shown) {
      ctx.save();
      ctx.setLineDash([4, 4]);
      ctx.strokeStyle = '#EF6C00';
      ctx.beginPath(); ctx.arc(cx, y, r, 0, Math.PI * 2); ctx.stroke();
      ctx.restore();
      drawText(ctx, '?', { x: cx - r, y: y - r, w: 2 * r, h: 2 * r }, '#EF6C00');
    }
    drawText(ctx, label, { x: cx - w / 2, y: y + r * 1.3, w, h: box.h * 0.2 });
  }
}

// Bean plants on days 0..shown, growing `per` cm a day; the last one is the question.
function plants(ctx, box, start, per, days, asked) {
  const all = [...days, asked];
  const w = box.w / all.length;
  const base = box.y + box.h * 0.75;
  const unit = (box.h * 0.6) / (start + per * asked);
  all.forEach((d, i) => {
    const cx = box.x + w * (i + 0.5);
    if (d === asked) {
      drawText(ctx, '?', { x: cx - w / 2, y: base - box.h * 0.45, w, h: box.h * 0.3 }, '#EF6C00');
    } else {
      const top = base - (start + per * d) * unit;
      ctx.strokeStyle = '#388E3C';
      ctx.lineWidth = 4;
      ctx.beginPath(); ctx.moveTo(cx, base); ctx.lineTo(cx, top); ctx.stroke();
      ctx.fillStyle = '#66BB6A';
      ctx.beginPath(); ctx.ellipse(cx + 7, top + 6, 7, 3.5, -0.5, 0, Math.PI * 2); ctx.fill();
      ctx.beginPath(); ctx.ellipse(cx - 7, top + 10, 7, 3.5, 0.5, 0, Math.PI * 2); ctx.fill();
      drawText(ctx, `${start + per * d} cm`, { x: cx - w / 2, y: top - box.h * 0.16, w, h: box.h * 0.12 });
    }
    drawText(ctx, `día ${d}`, { x: cx - w / 2, y: base + 4, w, h: box.h * 0.14 });
  });
  ctx.fillStyle = '#8D6E63';
  ctx.fillRect(box.x, base, box.w, 4);
}

// A strip of pieces going down, to compare how different rules look.
function strip(unit, len = 6) {
  return (ctx, box) => {
    ctx.fillStyle = '#FFF8E1';
    ctx.beginPath(); ctx.roundRect(box.x + box.w * 0.15, box.y, box.w * 0.7, box.h, 10); ctx.fill();
    const cell = box.h / len;
    for (let i = 0; i < len; i++) {
      const p = unit[i % unit.length];
      drawShape(ctx, p.kind, box.x + box.w / 2, box.y + cell * (i + 0.5), Math.min(cell, box.w * 0.6) * 0.4, p.color);
    }
  };
}

export default class PiensaPatronLesson extends ChoiceLesson {
  get intro() { return '¡A pensar como tejedores y jugadores!'; }
  get colors() { return ['#F3E5F5', '#E3F2FD']; }

  makeRounds() {
    const unit = [P('circle', RED), P('triangle', BLUE), P('triangle', BLUE)];
    const seq = Array.from({ length: 7 }, (_, i) => unit[i % unit.length]);
    const gap = 3;
    const answer = seq[gap];
    const beads = [RED, BLUE, BLUE];
    const asked = 10;
    const bead = beads[(asked - 1) % beads.length];
    const [start, per, day] = [3, 2, 4];
    const [saved, weeks] = [5, 6];
    const rule = [P('circle', RED), P('circle', RED), P('circle', BLUE)];
    const strips = [[P('circle', RED), P('circle', BLUE)], rule, [P('circle', RED), P('circle', BLUE), P('circle', BLUE)]];
    return [
      {
        say: 'En este tejido falta una pieza en medio. ¿Cuál va en el espacio vacío?',
        ask: '¿Qué pieza falta en el tejido?',
        hint: 'Busca cómo se repite el patrón y cuenta hasta el espacio vacío.',
        scene: (ctx, box, t) => band(ctx, box, seq, gap, t),
        choices: [answer, P('triangle', BLUE), P('square', YELLOW)]
          .filter((p, i, all) => all.findIndex((q) => same(p, q)) === i)
          .map((p) => ({ correct: same(p, answer), draw: piece(p) })),
      },
      {
        say: `Jugamos a hacer un collar: ${beads.map((c) => COLOR_WORD[c]).join(', ')}, y se repite. ¿De qué color es la cuenta número ${asked}?`,
        ask: `¿De qué color es la cuenta ${asked}?`,
        hint: `El patrón se repite cada ${beads.length} cuentas. Sigue contando desde la 7.`,
        scene: (ctx, box) => necklace(ctx, box, beads, 6, asked),
        choices: [RED, BLUE, YELLOW].map((c) => ({ value: COLOR_WORD[c], correct: c === bead, draw: piece(P('circle', c)) })),
      },
      {
        say: `Una planta de frijol crece ${per} centímetros cada día. El día 0 medía ${start} centímetros. ¿Cuánto medirá el día ${day}?`,
        ask: `¿Cuánto medirá el día ${day}?`,
        hint: `Cada día suma ${per} centímetros. Sigue la tabla hasta el día ${day}.`,
        scene: (ctx, box) => plants(ctx, box, start, per, [0, 1, 2], day),
        choices: pickChoices(start + per * day, [start + per * (day - 1), per * day], { draw: (ctx, v, box) => drawText(ctx, `${v} cm`, box) }),
      },
      {
        say: `Ana guarda ${saved} quetzales en su alcancía cada semana. Por eso su dinero crece siempre igual. ¿Cuánto tendrá en ${weeks} semanas?`,
        ask: `Q${saved} cada semana, ${weeks} semanas`,
        hint: `Cuenta de ${saved} en ${saved}, una vez por cada semana.`,
        choices: pickChoices(saved * weeks, [saved + weeks, saved * (weeks - 1)], { draw: (ctx, v, box) => drawText(ctx, `Q${v}`, box) }),
      },
      {
        say: 'La regla del tejido es: dos rojos y un azul, y se repite. ¿Qué tira sigue la regla?',
        ask: '¿Cuál es: dos rojos y un azul?',
        hint: 'Lee cada tira de arriba hacia abajo: rojo, rojo, azul, rojo, rojo, azul.',
        choices: strips.map((u) => ({ correct: u.length === rule.length && u.every((p, i) => same(p, rule[i])), draw: strip(u) })),
      },
    ];
  }
}
