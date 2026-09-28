// Nivel 4 · Recta Numérica y Comparación
// CNB Tercero, competencia 4 — 4.1.4 (comparación hasta 10,000: igual, menor, mayor), 4.1.3
// (numerales en la recta de 50 en 50, 100 en 100 y 1,000 en 1,000) y 4.1.1 (ordinales hasta el
// 40º, en numeración arábiga y maya). Distractor de la recta: leer 350 como 305.
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { drawMaya, drawText, num } from '../shared/draw.js';

function line(ctx, box, { max, step, every, at }) {
  const x0 = box.x + box.w * 0.07;
  const unit = (box.w * 0.86) / max;
  const y = box.y + box.h * 0.55;
  ctx.save();
  ctx.strokeStyle = '#37474F';
  ctx.fillStyle = '#37474F';
  ctx.lineWidth = 3;
  ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(x0 + max * unit, y); ctx.stroke();
  ctx.font = `bold ${Math.round(Math.min(box.h * 0.08, (every * unit) / 3.2))}px Nunito, sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  for (let v = 0; v <= max; v += step) {
    const big = v % every === 0;
    ctx.beginPath(); ctx.moveTo(x0 + v * unit, y - (big ? 12 : 7)); ctx.lineTo(x0 + v * unit, y + (big ? 12 : 7)); ctx.stroke();
    if (big) ctx.fillText(num(v), x0 + v * unit, y + 16);
  }
  ctx.fillStyle = '#E53935';
  const ax = x0 + at * unit;
  ctx.beginPath(); ctx.moveTo(ax, y - 14); ctx.lineTo(ax - 12, y - box.h * 0.25); ctx.lineTo(ax + 12, y - box.h * 0.25); ctx.closePath(); ctx.fill();
  ctx.restore();
}

const compare = (a, b) => (a < b ? '<' : a > b ? '>' : '=');

function pointer(max, step, every, at, wrongs) {
  return {
    say: `En esta recta, cada rayita suma ${num(step)}. ¿Qué número señala la flecha roja?`,
    ask: '¿Qué número señala la flecha?',
    hint: `Busca el número escrito antes de la flecha y cuenta de ${num(step)} en ${num(step)}.`,
    scene: (ctx, box) => line(ctx, box, { max, step, every, at }),
    choices: pickChoices(at, wrongs),
  };
}

export default class RectaCompararLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a ubicar y comparar números grandes!'; }
  get colors() { return ['#FFFDE7', '#E8F5E9']; }

  makeRounds() {
    const [a, b] = [4356, 4365];
    const nums = [7080, 7800, 7008];
    const smallest = Math.min(...nums);
    const [tens, units] = [30, 2];
    return [
      pointer(10000, 1000, 5000, 7000, [6000, 700]),
      pointer(500, 50, 100, 350, [305, 400]),
      {
        say: `¿Qué signo va en medio: ${num(a)} y ${num(b)}? ¿Mayor que, menor que o igual?`,
        ask: `${num(a)}  ?  ${num(b)}`,
        hint: 'Compara cifra por cifra desde la izquierda, hasta encontrar una diferente.',
        scene: (ctx, box) => drawText(ctx, `${num(a)}  ?  ${num(b)}`, { x: box.x, y: box.y + box.h * 0.3, w: box.w, h: box.h * 0.4 }),
        choices: pickChoices(compare(a, b), ['>', '=']),
      },
      {
        say: '¿Cuál de estos números es el MENOR?',
        ask: '¿Cuál número es menor?',
        hint: 'Todos tienen 7 unidades de millar. Mira las centenas, y después las decenas.',
        choices: pickChoices(smallest, nums),
      },
      {
        say: 'En la carrera, Ana llegó en el lugar vigésimo quinto. ¿Cómo se escribe ese lugar con números?',
        ask: '¿Cómo se escribe vigésimo quinto?',
        hint: 'Vigésimo es 20 y quinto es 5.',
        choices: pickChoices(`${20 + 5}º`, ['20º', '52º']),
      },
      {
        say: 'Luis llegó en el lugar trigésimo segundo. ¿Qué número maya muestra su lugar?',
        ask: '¿Cuál es el 32 en maya?',
        hint: `Trigésimo segundo es ${tens + units}: una veintena arriba y ${tens + units - 20} abajo.`,
        choices: pickChoices(tens + units, [23, 12], { draw: drawMaya }),
      },
    ];
  }
}
