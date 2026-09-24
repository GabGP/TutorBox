// Nivel 1 · Flores en la Regla
// CNB Segundo, competencia 1 — 1.2.4 (estimación y medición de distancias entre elementos de
// patrones utilizando el centímetro).
import { ChoiceLesson, numberChoices } from '../shared/choice-lesson.js';

const MAX_CM = 12;

function flower(ctx, cx, cy, r) {
  ctx.fillStyle = '#EC407A';
  for (let i = 0; i < 5; i++) {
    const a = (Math.PI * 2 * i) / 5;
    ctx.beginPath(); ctx.arc(cx + Math.cos(a) * r * 0.6, cy + Math.sin(a) * r * 0.6, r * 0.45, 0, Math.PI * 2); ctx.fill();
  }
  ctx.fillStyle = '#FDD835';
  ctx.beginPath(); ctx.arc(cx, cy, r * 0.35, 0, Math.PI * 2); ctx.fill();
}

// A ruler from 0 to MAX_CM with a flower above each mark in `at`.
function ruler(ctx, box, at) {
  const cm = (box.w * 0.9) / MAX_CM;
  const x0 = box.x + box.w * 0.05;
  const top = box.y + box.h * 0.62;
  ctx.fillStyle = '#FFE082';
  ctx.strokeStyle = '#8D6E63';
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.roundRect(x0 - 8, top, cm * MAX_CM + 16, box.h * 0.3, 6); ctx.fill(); ctx.stroke();
  ctx.fillStyle = '#4E342E';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  ctx.font = `bold ${Math.round(cm * 0.55)}px Nunito, sans-serif`;
  for (let i = 0; i <= MAX_CM; i++) {
    ctx.beginPath(); ctx.moveTo(x0 + i * cm, top); ctx.lineTo(x0 + i * cm, top + box.h * 0.1); ctx.stroke();
    ctx.fillText(String(i), x0 + i * cm, top + box.h * 0.13);
  }
  at.forEach((c) => {
    ctx.strokeStyle = '#43A047';
    ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(x0 + c * cm, top); ctx.lineTo(x0 + c * cm, box.y + box.h * 0.35); ctx.stroke();
    flower(ctx, x0 + c * cm, box.y + box.h * 0.25, Math.min(cm * 0.7, box.h * 0.13));
  });
}

// ask: 'step' = how far apart the flowers are; 'next' = where the next flower goes.
const ROUNDS = [
  { start: 0, step: 2, count: 4, ask: 'step' },
  { start: 1, step: 3, count: 3, ask: 'next' },
  { start: 0, step: 4, count: 3, ask: 'step' },
  { start: 2, step: 2, count: 4, ask: 'next' },
];

export default class PatronReglaLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a medir un patrón de flores con la regla!'; }
  get colors() { return ['#F3E5F5', '#FFFDE7']; }

  makeRounds() {
    return ROUNDS.map(({ start, step, count, ask }) => {
      const at = Array.from({ length: count }, (_, i) => start + i * step);
      const scene = (ctx, box) => ruler(ctx, box, at);
      if (ask === 'step') {
        return {
          say: 'Las flores están sembradas en patrón. ¿Cada cuántos centímetros hay una flor?',
          ask: '¿Cada cuántos cm hay una flor?',
          hint: 'Mira el número de una flor y el de la siguiente. ¿Cuántos centímetros hay entre ellas?',
          scene,
          choices: numberChoices(step, { min: 1, max: MAX_CM }),
        };
      }
      return {
        say: `Hay una flor cada ${step} centímetros. ¿En qué centímetro va la siguiente flor?`,
        ask: '¿Dónde va la siguiente flor?',
        hint: `Busca la última flor y cuenta ${step} centímetros más.`,
        scene,
        choices: numberChoices(start + count * step, { max: MAX_CM }),
      };
    });
  }
}
