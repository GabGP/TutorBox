// Nivel 2 · Antes y Después
// CNB Segundo, competencia 2 — 2.1.2 (descripción de eventos y sucesos en función del tiempo) y
// 2.1.1 (cambios de posición en relación con un mismo punto de referencia).
import { ChoiceLesson } from '../shared/choice-lesson.js';
import { drawEmoji } from '../shared/draw.js';
import { elote, gallina, pollito } from '../shared/art.js';

// Three steps in time order with one hidden; the child picks the hidden one.
function sequence(ctx, box, steps, hidden, t) {
  const cell = box.w / steps.length;
  steps.forEach((s, i) => {
    const cx = box.x + cell * (i + 0.5);
    const cy = box.y + box.h / 2;
    if (i === hidden) {
      ctx.save();
      ctx.setLineDash([6, 5]);
      ctx.strokeStyle = `rgba(0,0,0,${0.35 + Math.sin(t * 4) * 0.2})`;
      ctx.lineWidth = 3;
      ctx.beginPath(); ctx.roundRect(cx - cell * 0.35, cy - cell * 0.35, cell * 0.7, cell * 0.7, 10); ctx.stroke();
      ctx.restore();
    } else {
      drawEmoji(ctx, s, cx, cy, Math.min(cell, box.h) * 0.6);
    }
    if (i < steps.length - 1) drawEmoji(ctx, '➡️', box.x + cell * (i + 1), cy, cell * 0.22);
  });
}

// A tree in the middle with the chick left or right of it.
function side(where) {
  return (ctx, box) => {
    const cy = box.y + box.h * 0.55;
    const s = Math.min(box.w, box.h);
    drawEmoji(ctx, '🌳', box.x + box.w / 2, cy - s * 0.1, s * 0.5);
    drawEmoji(ctx, pollito, box.x + box.w * (where === 'left' ? 0.17 : 0.83), cy + s * 0.12, s * 0.3);
  };
}

const card = (item, correct) => ({
  correct,
  draw: (ctx, box) => drawEmoji(ctx, item, box.x + box.w / 2, box.y + box.h / 2, Math.min(box.w, box.h) * 0.75),
});

function missing(say, steps, hidden, wrong) {
  return {
    say,
    ask: '¿Qué va en el espacio vacío?',
    hint: 'Piensa qué pasa primero, qué pasa después y qué pasa al final.',
    scene: (ctx, box, t) => sequence(ctx, box, steps, hidden, t),
    choices: [card(steps[hidden], true), ...wrong.map((w) => card(w, false))],
  };
}

export default class AntesDespuesLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a ordenar lo que pasa primero y lo que pasa después!'; }
  get colors() { return ['#E8F5E9', '#FFF8E1']; }

  makeRounds() {
    return [
      missing('Primero hay un huevo y al final una gallina. ¿Qué pasa en medio?', ['🥚', pollito, gallina], 1, [elote, '🥚']),
      missing('Sembramos la semilla y crece la milpa. ¿Qué cosechamos al final?', ['🌱', '🌿', elote], 2, ['🌱', pollito]),
      missing('Mira cómo pasa el día. ¿Qué pasa primero, en la mañana?', ['🌅', '☀️', '🌙'], 0, ['🌙', '⭐']),
      {
        say: 'El pollito está a la izquierda del árbol. Camina y pasa al otro lado del árbol. ¿Dónde está ahora?',
        ask: '¿Dónde está el pollito ahora?',
        hint: 'Si pasa al otro lado, ya no está donde empezó.',
        scene: side('left'),
        choices: [
          { correct: true, draw: side('right') },
          { correct: false, draw: side('left') },
        ],
      },
    ];
  }
}
