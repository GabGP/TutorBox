// Módulo 2 · Patrones de Números
// CNB Primero 4.1.5 (contar de 2 en 2 y de 5 en 5) y 4.4.2 (series ascendentes y descendentes).
import { ChoiceLesson, numberChoices } from '../shared/choice-lesson.js';
import { drawEmoji, drawNumeral } from '../shared/draw.js';

// Each series is start + step: the missing number is computed, never typed by hand.
const SERIES = [
  { start: 1, step: 1, how: 'de uno en uno' },
  { start: 2, step: 2, how: 'de dos en dos' },
  { start: 9, step: -1, how: 'hacia atrás' },
  { start: 0, step: 5, how: 'de cinco en cinco' },
];

function river(ctx, box, shown, t) {
  const slots = [...shown, '?'];
  const cell = box.w / slots.length;
  const r = Math.min(cell * 0.42, box.h * 0.2);
  const y = box.y + box.h * 0.65;
  ctx.fillStyle = '#4FC3F7';
  ctx.beginPath(); ctx.roundRect(box.x, y - r * 1.3, box.w, r * 2.6, 18); ctx.fill();
  slots.forEach((value, i) => {
    const cx = box.x + cell * (i + 0.5);
    const missing = value === '?';
    const bob = missing ? Math.sin(t * 4) * 3 : 0;
    ctx.fillStyle = missing ? '#FFE082' : '#78909C';
    ctx.beginPath(); ctx.ellipse(cx, y + bob, r, r * 0.8, 0, 0, Math.PI * 2); ctx.fill();
    drawNumeral(ctx, value, { x: cx - r, y: y - r + bob, w: r * 2, h: r * 2 }, missing ? '#E65100' : '#FFFFFF');
  });
  // The frog waits on the last stone it knows, ready to jump to the next one.
  drawEmoji(ctx, '🐸', box.x + cell * (shown.length - 0.5), y - r * 1.7, r * 1.2);
}

export default class PatronesNumerosLesson extends ChoiceLesson {
  get intro() { return '¡Ayuda a la rana a cruzar el río!'; }
  get colors() { return ['#E1F5FE', '#C8E6C9']; }

  makeRounds() {
    return SERIES.map(({ start, step, how }) => {
      const shown = [0, 1, 2, 3].map((i) => start + i * step);
      const answer = start + 4 * step;
      return {
        say: `Mira las piedras: ${shown.join(', ')}. Contamos ${how}. ¿Qué número sigue?`,
        ask: `${shown.join(', ')}, ?`,
        hint: `Cuenta ${how} otra vez, desde la primera piedra.`,
        scene: (ctx, box, t) => river(ctx, box, shown, t),
        choices: numberChoices(answer, { max: 25 }),
      };
    });
  }
}
