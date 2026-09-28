// Nivel 7 · Geme, Paso y Brazada
// CNB Tercero, competencia 7 — 7.1.1 (estimación y medición de longitud con geme, paso y brazada)
// y 7.1.2 (relación entre esas medidas y el metro y el centímetro). El tamaño de cada medida
// cambia según la persona: en los problemas se dice cuánto mide.
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { drawEmoji, drawText } from '../shared/draw.js';

/** Arms stretched out: a brazada. */
function brazada(ctx, cx, cy, size) {
  const s = size / 2;
  ctx.save();
  ctx.strokeStyle = '#5D4037';
  ctx.fillStyle = '#5D4037';
  ctx.lineWidth = Math.max(3, s * 0.1);
  ctx.lineCap = 'round';
  ctx.beginPath(); ctx.arc(cx, cy - s * 0.55, s * 0.18, 0, Math.PI * 2); ctx.fill();
  ctx.beginPath();
  ctx.moveTo(cx, cy - s * 0.35); ctx.lineTo(cx, cy + s * 0.25);
  ctx.moveTo(cx - s * 0.9, cy - s * 0.25); ctx.lineTo(cx + s * 0.9, cy - s * 0.25);
  ctx.moveTo(cx, cy + s * 0.25); ctx.lineTo(cx - s * 0.3, cy + s * 0.8);
  ctx.moveTo(cx, cy + s * 0.25); ctx.lineTo(cx + s * 0.3, cy + s * 0.8);
  ctx.stroke();
  ctx.restore();
}

// Rough length of each measure for a grown-up, only used to order them.
const UNITS = { geme: { art: '🖐️', cm: 20 }, paso: { art: '👣', cm: 60 }, brazada: { art: brazada, cm: 160 } };
// The measure that fits each thing best.
const BEST = { aula: 'paso', pozo: 'brazada' };

function unit(name) {
  return (ctx, box) => {
    drawEmoji(ctx, UNITS[name].art, box.x + box.w / 2, box.y + box.h * 0.4, Math.min(box.w, box.h) * 0.55);
    drawText(ctx, name, { x: box.x, y: box.y + box.h * 0.74, w: box.w, h: box.h * 0.2 });
  };
}

const units = (test) => Object.keys(UNITS).map((name) => ({ value: name, correct: test(name), draw: unit(name) }));
const cm = (ctx, v, box) => drawText(ctx, `${v} cm`, box);

export default class GemePasoLesson extends ChoiceLesson {
  get intro() { return '¡Los abuelos medían con el cuerpo: gemes, pasos y brazadas!'; }
  get colors() { return ['#E1F5FE', '#F1F8E9']; }

  makeRounds() {
    const longest = Object.keys(UNITS).reduce((a, b) => (UNITS[b].cm > UNITS[a].cm ? b : a));
    const [gemes, geme] = [6, 20];
    const [steps, step] = [4, 50];
    return [
      {
        say: 'El geme es la mano abierta, el paso es lo que avanzas al caminar y la brazada son los brazos abiertos. ¿Cuál es la medida más larga?',
        ask: '¿Cuál medida es la más larga?',
        hint: 'Abre tu mano, da un paso y abre los brazos. ¿Qué mide más?',
        choices: units((name) => name === longest),
      },
      {
        say: '¿Con qué medirías el largo del aula?',
        ask: '¿Con qué mides el aula?',
        hint: 'El aula es larga y la recorres caminando.',
        choices: units((name) => name === BEST.aula),
      },
      {
        say: '¿Y con qué medirías una cuerda larga, como la del pozo?',
        ask: '¿Con qué mides la cuerda del pozo?',
        hint: 'La cuerda se estira entre los brazos abiertos, una y otra vez.',
        choices: units((name) => name === BEST.pozo),
      },
      {
        say: `La mesa mide ${gemes} gemes. El geme de la maestra mide ${geme} centímetros. ¿Cuántos centímetros mide la mesa?`,
        ask: `${gemes} gemes de ${geme} cm`,
        hint: `Suma ${geme} centímetros por cada geme.`,
        choices: pickChoices(gemes * geme, [gemes + geme, gemes * 2], { draw: cm }),
      },
      {
        say: `Un paso de Ana mide ${step} centímetros. Ana dio ${steps} pasos. ¿Cuántos centímetros caminó?`,
        ask: `${steps} pasos de ${step} cm`,
        hint: `Suma ${step} centímetros por cada paso. Cada 100 centímetros son un metro.`,
        choices: pickChoices(steps * step, [steps + step, (steps + 1) * step], { draw: cm }),
      },
    ];
  }
}
