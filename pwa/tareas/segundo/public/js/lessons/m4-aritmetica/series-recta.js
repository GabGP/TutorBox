// Nivel 4 · Series y Recta Numérica
// CNB Segundo, competencia 4 — 4.5.1 (completación de series de 4 en 4, 100 en 100), 4.6.1
// (numerales en la recta numérica), 4.6.2 (antecesor y sucesor), 4.6.3 (mayor que) y 4.2.1
// (números ordinales).
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { drawEmoji, drawText } from '../shared/draw.js';
import { cerdo, gallina, pollito, vaca } from '../shared/art.js';

function cards(ctx, box, items, t) {
  const w = box.w / items.length;
  items.forEach((n, i) => {
    const b = { x: box.x + w * i + 4, y: box.y + box.h * 0.3, w: w - 8, h: box.h * 0.4 };
    ctx.save();
    ctx.fillStyle = n === null ? `rgba(255,255,255,${0.5 + Math.sin(t * 4) * 0.2})` : '#FFFFFF';
    ctx.beginPath(); ctx.roundRect(b.x, b.y, b.w, b.h, 10); ctx.fill();
    ctx.restore();
    drawText(ctx, n === null ? '?' : n, b);
  });
}

// `wrongs` are hand-picked mistakes (one too many, one step too far); the answer is computed.
function series(start, step, wrongs) {
  const seq = [0, 1, 2, 3].map((i) => start + i * step);
  return {
    say: `Esta serie va de ${step} en ${step}. ¿Qué número sigue?`,
    ask: `${seq.join(', ')}, ¿?`,
    hint: `Al último número súmale ${step}.`,
    scene: (ctx, box, t) => cards(ctx, box, [...seq, null], t),
    choices: pickChoices(start + 4 * step, wrongs),
  };
}

// A number line from 0 to 100, only 0, 50 and 100 written, with an arrow on `at`.
function line(ctx, box, at) {
  const x0 = box.x + box.w * 0.06;
  const unit = (box.w * 0.88) / 100;
  const y = box.y + box.h * 0.55;
  ctx.save();
  ctx.strokeStyle = '#37474F';
  ctx.fillStyle = '#37474F';
  ctx.lineWidth = 3;
  ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(x0 + 100 * unit, y); ctx.stroke();
  ctx.font = `bold ${Math.round(box.h * 0.1)}px Nunito, sans-serif`;
  ctx.textAlign = 'center';
  for (let v = 0; v <= 100; v += 10) {
    ctx.beginPath(); ctx.moveTo(x0 + v * unit, y - 10); ctx.lineTo(x0 + v * unit, y + 10); ctx.stroke();
    if (v % 50 === 0) ctx.fillText(String(v), x0 + v * unit, y + box.h * 0.2);
  }
  ctx.fillStyle = '#E53935';
  const ax = x0 + at * unit;
  ctx.beginPath(); ctx.moveTo(ax, y - 14); ctx.lineTo(ax - 12, y - box.h * 0.25); ctx.lineTo(ax + 12, y - box.h * 0.25); ctx.closePath(); ctx.fill();
  ctx.restore();
}

const ROW = [vaca, gallina, cerdo, pollito];
const art = (a) => (ctx, box) => drawEmoji(ctx, a, box.x + box.w / 2, box.y + box.h / 2, Math.min(box.w, box.h) * 0.8);

export default class SeriesRectaLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a jugar con series y con la recta numérica!'; }
  get colors() { return ['#FFFDE7', '#E8F5E9']; }

  makeRounds() {
    const at = 70;
    const nums = [507, 570, 75];
    const place = 3;
    return [
      series(8, 4, [21, 28]),
      series(300, 100, [610, 800]),
      {
        say: 'La recta va de 0 a 100 y cada rayita suma 10. ¿Qué número señala la flecha roja?',
        ask: '¿Qué número señala la flecha?',
        hint: 'Cuenta las rayitas de 10 en 10 desde el cero: 10, 20, 30...',
        scene: (ctx, box) => line(ctx, box, at),
        choices: pickChoices(at, [at - 10, at + 10]),
      },
      {
        say: '¿Qué número viene justo después del 399?',
        ask: '¿Qué número sigue después de 399?',
        hint: 'Después de 9 unidades viene una decena nueva, y después de 9 decenas, una centena nueva.',
        choices: pickChoices(399 + 1, [398, 3910]),
      },
      {
        say: '¿Cuál de estos números es el MAYOR?',
        ask: '¿Cuál número es mayor?',
        hint: 'Primero mira las centenas. Si son iguales, mira las decenas.',
        choices: pickChoices(Math.max(...nums), nums),
      },
      {
        say: 'Los animales hacen fila desde la bandera. ¿Quién está en el TERCER lugar?',
        ask: '¿Quién está en el tercer lugar?',
        hint: 'Cuenta desde la bandera: primero, segundo, tercero.',
        scene: (ctx, box) => {
          const w = box.w / (ROW.length + 1);
          drawEmoji(ctx, '🚩', box.x + w / 2, box.y + box.h / 2, w * 0.7);
          ROW.forEach((a, i) => drawEmoji(ctx, a, box.x + w * (i + 1.5), box.y + box.h / 2, w * 0.85));
        },
        choices: [ROW[place - 1], ROW[place - 2], ROW[place]].map((a, i) => ({ correct: i === 0, draw: art(a) })),
      },
    ];
  }
}
