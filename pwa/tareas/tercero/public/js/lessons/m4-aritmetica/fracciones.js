// Nivel 4 · Comparar Fracciones
// CNB Tercero, competencia 4 — 4.4.2 (comparación de fracciones), 4.4.1 (significado de una
// fracción) y 4.4.3 (fracciones con numerador 1 en la recta numérica). Distractor clave: creer que
// 1/5 es mayor que 1/3 porque 5 es mayor que 3.
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { center, drawText, inset } from '../shared/draw.js';

const text = ([n, d]) => `${n}/${d}`;
// Cross-multiplying compares n1/d1 with n2/d2 without decimals.
const compare = ([n1, d1], [n2, d2]) => (n1 * d2 < n2 * d1 ? '<' : n1 * d2 > n2 * d1 ? '>' : '=');

/** A tortilla cut in `parts` equal slices, `shaded` of them painted. */
function pie(ctx, box, parts, shaded) {
  const { cx, cy } = center(box);
  const r = Math.min(box.w, box.h) * 0.45;
  for (let i = 0; i < parts; i++) {
    const a0 = -Math.PI / 2 + (Math.PI * 2 * i) / parts;
    ctx.fillStyle = i < shaded ? '#FFB300' : '#FFF3D6';
    ctx.beginPath(); ctx.moveTo(cx, cy); ctx.arc(cx, cy, r, a0, a0 + (Math.PI * 2) / parts); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = '#8D6E63';
    ctx.lineWidth = 3;
    ctx.stroke();
  }
}

/** "3/4" the school way: numerator, line, denominator. */
function fraction(ctx, value, box) {
  const [top, bottom] = value.split('/');
  const half = { ...box, h: box.h / 2 };
  drawText(ctx, top, inset(half, 0.15, 0.1));
  drawText(ctx, bottom, inset({ ...half, y: box.y + box.h / 2 }, 0.15, 0.1));
  ctx.fillStyle = '#1F2A1F';
  ctx.fillRect(box.x + box.w * 0.3, box.y + box.h / 2 - 2, box.w * 0.4, 4);
}

/** A number line from 0 to 1 cut in `parts` equal pieces, with an arrow on the first mark. */
function unitLine(ctx, box, parts) {
  const x0 = box.x + box.w * 0.08;
  const len = box.w * 0.84;
  const y = box.y + box.h * 0.55;
  ctx.strokeStyle = '#37474F';
  ctx.lineWidth = 3;
  ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(x0 + len, y); ctx.stroke();
  for (let i = 0; i <= parts; i++) {
    ctx.beginPath(); ctx.moveTo(x0 + (len * i) / parts, y - 10); ctx.lineTo(x0 + (len * i) / parts, y + 10); ctx.stroke();
  }
  drawText(ctx, 0, { x: x0 - 20, y: y + 14, w: 40, h: box.h * 0.15 });
  drawText(ctx, 1, { x: x0 + len - 20, y: y + 14, w: 40, h: box.h * 0.15 });
  const ax = x0 + len / parts;
  ctx.fillStyle = '#E53935';
  ctx.beginPath(); ctx.moveTo(ax, y - 14); ctx.lineTo(ax - 11, y - box.h * 0.25); ctx.lineTo(ax + 11, y - box.h * 0.25); ctx.closePath(); ctx.fill();
}

function bigger(a, b, say, hint, scene) {
  const answer = compare(a, b) === '>' ? a : b;
  return {
    say,
    ask: `¿Cuál es mayor: ${text(a)} o ${text(b)}?`,
    hint,
    scene,
    choices: [a, b].map((f) => ({ value: text(f), correct: f === answer, draw: (ctx, box) => fraction(ctx, text(f), box) })),
  };
}

export default class FraccionesLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a comparar pedazos de tortilla!'; }
  get colors() { return ['#FFFDE7', '#FBE9E7']; }

  makeRounds() {
    const [parts, shaded] = [5, 3];
    const third = [1, 3];
    const fifth = [1, 5];
    const [x, y] = [[3, 8], [3, 4]];
    const cut = 4;
    return [
      {
        say: `La tortilla se partió en ${parts} partes iguales y se comieron las partes pintadas. ¿Qué fracción se comieron?`,
        ask: '¿Qué fracción está pintada?',
        hint: 'Arriba va cuántas partes están pintadas. Abajo, en cuántas partes iguales se partió.',
        scene: (ctx, box) => pie(ctx, box, parts, shaded),
        choices: pickChoices(text([shaded, parts]), [text([parts - shaded, parts]), text([shaded, parts - shaded])], { draw: fraction }),
      },
      bigger(third, fifth,
        'Partimos dos tortillas iguales: una en 3 partes y otra en 5. ¿Qué pedazo es más grande?',
        'Mientras en más partes se corta la tortilla, más pequeño es cada pedazo.',
        (ctx, box) => {
          pie(ctx, { ...box, w: box.w / 2 }, third[1], 1);
          pie(ctx, { ...box, x: box.x + box.w / 2, w: box.w / 2 }, fifth[1], 1);
        }),
      bigger([2, 7], [5, 7], '¿Qué fracción es mayor: dos séptimos o cinco séptimos?',
        'Las dos tienen partes del mismo tamaño, séptimos. Gana la que tiene más partes.'),
      {
        say: '¿Qué signo va en medio: tres octavos y tres cuartos?',
        ask: `${text(x)}  ?  ${text(y)}`,
        hint: 'Las dos tienen 3 partes. Un cuarto es más grande que un octavo.',
        scene: (ctx, box) => {
          const w = box.w / 3;
          fraction(ctx, text(x), inset({ ...box, w }, 0.2, 0.15));
          drawText(ctx, '?', { x: box.x + w, y: box.y, w, h: box.h }, '#EF6C00');
          fraction(ctx, text(y), inset({ ...box, x: box.x + 2 * w, w }, 0.2, 0.15));
        },
        choices: pickChoices(compare(x, y), ['>', '=']),
      },
      {
        say: `La recta del 0 al 1 está partida en ${cut} partes iguales. ¿Qué fracción señala la flecha?`,
        ask: '¿Qué fracción señala la flecha?',
        hint: 'Cuenta los espacios entre el 0 y el 1, no las rayitas.',
        scene: (ctx, box) => unitLine(ctx, box, cut),
        choices: pickChoices(text([1, cut]), [text([1, cut - 1]), text([cut, 1])], { draw: fraction }),
      },
    ];
  }
}
