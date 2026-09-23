// Módulo 7 · Días de la Semana
// CNB Primero 7.3.1 (semanas y meses del calendario), 4.5.1 (antecesor y sucesor) y 7.2.2 (actividades y tiempo).
import { ChoiceLesson, numberChoices } from '../shared/choice-lesson.js';
import { center, drawEmoji } from '../shared/draw.js';

const DAYS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'];
const INITIALS = ['L', 'M', 'M', 'J', 'V', 'S', 'D'];
const COLORS = ['#E53935', '#FB8C00', '#FDD835', '#43A047', '#1E88E5', '#8E24AA', '#EC407A'];

function dayBadge(ctx, box, i, today) {
  const { cx, cy } = center(box);
  const r = Math.min(box.w, box.h) * 0.46;
  ctx.fillStyle = COLORS[i];
  ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.fill();
  if (today) {
    ctx.strokeStyle = '#1F2A1F';
    ctx.lineWidth = 4;
    ctx.stroke();
    drawEmoji(ctx, '⭐', cx, cy - r * 1.55, r * 0.9);
  }
  ctx.fillStyle = '#FFFFFF';
  ctx.font = `900 ${Math.round(r * 1.1)}px Nunito, sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(INITIALS[i], cx, cy + 1);
}

// The whole week as tappable badges; `today` gets a star above it.
function weekChoices(today, answer) {
  return DAYS.map((day, i) => ({
    correct: i === answer,
    hint: `Ese es el ${day}. Busca el día que viene después del ${DAYS[today]}.`,
    at: { x: 0.04 + i * 0.1314, y: 0.3, w: 0.125, h: 0.12 },
    draw: (ctx, box) => dayBadge(ctx, box, i, i === today),
  }));
}

export default class DiasSemanaLesson extends ChoiceLesson {
  get intro() { return '¡Aprendamos los días de la semana!'; }
  get colors() { return ['#E1F5FE', '#E8EAF6']; }

  makeRounds() {
    const tomorrow = (i) => (i + 1) % DAYS.length;
    const week = (ctx, box) => {
      const cell = box.w / DAYS.length;
      DAYS.forEach((_, i) => dayBadge(ctx, { x: box.x + cell * i, y: box.y + box.h * 0.35, w: cell, h: cell }, i, false));
    };
    return [
      {
        say: `La semana tiene estos días: ${DAYS.slice(0, 6).join(', ')} y domingo. ¿Cuántos días tiene la semana?`,
        ask: '¿Cuántos días tiene la semana?',
        hint: 'Cuenta los círculos de colores, uno por uno.',
        scene: week,
        choices: numberChoices(DAYS.length, { max: 9 }),
      },
      {
        say: 'Hoy es lunes: tiene una estrella. ¿Qué día es mañana? Toca el día que sigue.',
        ask: 'Hoy es lunes. ¿Qué día es mañana?',
        scene: () => {},
        choices: weekChoices(0, tomorrow(0)),
      },
      {
        say: 'Hoy es viernes. ¿Qué día es mañana? Toca el día que sigue.',
        ask: 'Hoy es viernes. ¿Qué día es mañana?',
        scene: () => {},
        choices: weekChoices(4, tomorrow(4)),
      },
      {
        say: '¿Cuándo duermes: en el día o en la noche?',
        ask: '¿Cuándo duermes?',
        hint: 'Cuando sale la luna y todo está oscuro, vamos a dormir.',
        choices: [
          { correct: false, draw: (ctx, box) => drawEmoji(ctx, '☀️', box.x + box.w / 2, box.y + box.h / 2, Math.min(box.w, box.h) * 0.6) },
          { correct: true, draw: (ctx, box) => drawEmoji(ctx, '🌙', box.x + box.w / 2, box.y + box.h / 2, Math.min(box.w, box.h) * 0.6) },
        ],
      },
    ];
  }
}
