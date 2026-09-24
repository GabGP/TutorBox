// Nivel 4 · Fracciones
// CNB Segundo, competencia 4 — 4.10.3 (representación gráfica de fracciones), 4.10.1 (partes
// iguales de la unidad, de medios a décimos) y 4.10.2 (significado de cada parte de la fracción).
// Distractores: contar las partes sin pintar, o poner pintadas sobre sin pintar (1/4 -> 1/3).
import { ChoiceLesson, numberChoices, pickChoices } from '../shared/choice-lesson.js';
import { center, drawText, inset } from '../shared/draw.js';

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

/** A chocolate bar in `parts` equal pieces. */
function bar(ctx, box, parts, shaded) {
  const w = (box.w * 0.9) / parts;
  const h = Math.min(box.h * 0.5, w * 1.6);
  const x0 = box.x + box.w * 0.05;
  const y0 = box.y + (box.h - h) / 2;
  for (let i = 0; i < parts; i++) {
    ctx.fillStyle = i < shaded ? '#6D4C41' : '#D7CCC8';
    ctx.strokeStyle = '#3E2723';
    ctx.lineWidth = 3;
    ctx.beginPath(); ctx.rect(x0 + i * w, y0, w, h); ctx.fill(); ctx.stroke();
  }
}

/** "3/4" drawn the school way: numerator, line, denominator. */
function fraction(ctx, value, box) {
  const [top, bottom] = value.split('/');
  const half = { ...box, h: box.h / 2 };
  drawText(ctx, top, inset(half, 0.15, 0.1));
  drawText(ctx, bottom, inset({ ...half, y: box.y + box.h / 2 }, 0.15, 0.1));
  ctx.fillStyle = '#1F2A1F';
  ctx.fillRect(box.x + box.w * 0.3, box.y + box.h / 2 - 2, box.w * 0.4, 4);
}

function whatFraction(parts, shaded, draw, say) {
  const answer = `${shaded}/${parts}`;
  const wrongs = [...new Set([`${parts - shaded}/${parts}`, `${shaded}/${parts - shaded}`, `${parts}/${shaded}`])]
    .filter((v) => v !== answer).slice(0, 2);
  return {
    say,
    ask: '¿Qué fracción está pintada?',
    hint: 'Arriba va cuántas partes están pintadas. Abajo, en cuántas partes iguales se partió.',
    scene: (ctx, box) => draw(ctx, box, parts, shaded),
    choices: pickChoices(answer, wrongs, { draw: fraction }),
  };
}

export default class FraccionesLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a partir tortillas en partes iguales!'; }
  get colors() { return ['#FFFDE7', '#FBE9E7']; }

  makeRounds() {
    const third = [3, 1];
    return [
      whatFraction(2, 1, pie, 'Partimos la tortilla en 2 partes iguales y Luis comió la parte pintada. ¿Qué fracción comió?'),
      whatFraction(4, 1, pie, 'Esta tortilla se partió en 4 partes iguales. ¿Qué fracción está pintada?'),
      whatFraction(4, 3, pie, 'Mira la tortilla. ¿Qué fracción está pintada ahora?'),
      whatFraction(5, 2, bar, 'Este chocolate tiene 5 partes iguales. ¿Qué fracción está pintada?'),
      {
        say: '¿Qué tortilla muestra un tercio? Un tercio es una parte de tres partes iguales.',
        ask: '¿Cuál muestra 1/3?',
        hint: 'Busca la tortilla partida en 3, con 1 parte pintada.',
        choices: [third, [4, 1], [3, 2]].map(([parts, shaded]) => ({
          value: `${shaded}/${parts}`,
          correct: parts === third[0] && shaded === third[1],
          draw: (ctx, box) => pie(ctx, box, parts, shaded),
        })),
      },
      {
        say: 'El número de abajo de la fracción dice en cuántas partes iguales se partió. ¿En cuántas partes se partió este pastel?',
        ask: '¿En cuántas partes iguales se partió?',
        hint: 'Cuenta todas las partes, pintadas y sin pintar.',
        scene: (ctx, box) => pie(ctx, box, 8, 3),
        choices: numberChoices(8, { min: 2, max: 10 }),
      },
    ];
  }
}
