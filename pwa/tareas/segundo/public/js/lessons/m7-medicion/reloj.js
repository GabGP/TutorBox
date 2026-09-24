// Nivel 7 · El Reloj
// CNB Segundo, competencia 7 — 7.4.1 (lectura del reloj: en punto, cuarto de hora antes y
// después, media hora) y 7.4.2 (ubicación temporal de actividades: horas y días).
// Distractor principal: leer la aguja corta como minutos y la larga como horas.
import { ChoiceLesson, pickChoices, stacked } from '../shared/choice-lesson.js';
import { center } from '../shared/draw.js';

const label = (h, m) => `${h}:${String(m).padStart(2, '0')}`;
const swapped = (h, m) => [m / 5 || 12, (h % 12) * 5];
const DAYS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'];

function clock(ctx, box, h, m) {
  const { cx, cy } = center(box);
  const r = Math.min(box.w, box.h) * 0.45;
  ctx.save();
  ctx.fillStyle = '#FFFFFF';
  ctx.strokeStyle = '#01579B';
  ctx.lineWidth = Math.max(3, r * 0.08);
  ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
  ctx.fillStyle = '#1F2A1F';
  ctx.font = `bold ${Math.round(r * 0.24)}px Nunito, sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  for (let n = 1; n <= 12; n++) {
    const a = (n * Math.PI) / 6 - Math.PI / 2;
    ctx.fillText(String(n), cx + Math.cos(a) * r * 0.78, cy + Math.sin(a) * r * 0.78);
  }
  const hand = (turns, len, width, color) => {
    const a = turns * Math.PI * 2 - Math.PI / 2;
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + Math.cos(a) * len, cy + Math.sin(a) * len); ctx.stroke();
  };
  hand(((h % 12) + m / 60) / 12, r * 0.45, Math.max(4, r * 0.1), '#D32F2F');
  hand(m / 60, r * 0.7, Math.max(3, r * 0.06), '#1F2A1F');
  ctx.fillStyle = '#1F2A1F';
  ctx.beginPath(); ctx.arc(cx, cy, r * 0.06, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}

function read(h, m, words) {
  return {
    say: 'La aguja corta y roja marca la hora. La larga marca los minutos. ¿Qué hora es?',
    ask: '¿Qué hora marca el reloj?',
    hint: `Primero mira la aguja corta, después la larga. Es ${words}.`,
    scene: (ctx, box) => clock(ctx, box, h, m),
    choices: pickChoices(label(h, m), [label(...swapped(h, m)), label(h, (m + 30) % 60)]),
  };
}

// Stacked clocks are not shuffled: the right one goes in position `slot`.
function show([h, m], words, others, slot) {
  return {
    say: `¿Qué reloj marca ${words}?`,
    ask: `¿Cuál marca ${words}?`,
    hint: 'La aguja corta marca la hora, la larga los minutos. Media hora: la larga en el 6. Y cuarto: en el 3. Menos cuarto: en el 9.',
    choices: stacked([...others.slice(0, slot), [h, m], ...others.slice(slot)].map(([hh, mm]) => ({
      value: label(hh, mm),
      correct: hh === h && mm === m,
      draw: (ctx, box) => clock(ctx, box, hh, mm),
    }))),
  };
}

export default class RelojLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a leer el reloj de la iglesia del pueblo!'; }
  get colors() { return ['#E1F5FE', '#FFF8E1']; }

  makeRounds() {
    const [start, later] = [8, 2];
    const today = 0;
    return [
      read(3, 0, 'las 3 en punto'),
      show([4, 30], 'las 4 y media', [swapped(4, 30), [5, 30]], 2),
      read(7, 15, 'las 7 y cuarto'),
      show([5, 45], 'las 6 menos cuarto', [[6, 15], [6, 45]], 0),
      {
        say: `La escuela empieza a las ${start}. El recreo es ${later} horas después. ¿A qué hora es el recreo?`,
        ask: `${start}:00 y ${later} horas después`,
        hint: `Cuenta ${later} horas desde las ${start}.`,
        choices: pickChoices(label(start + later, 0), [label(start - later, 0), label(start + 1, 0)]),
      },
      {
        say: `Hoy es ${DAYS[today]}. ¿Qué día es mañana?`,
        ask: `Hoy es ${DAYS[today]}. ¿Y mañana?`,
        hint: 'Di los días en orden: lunes, martes, miércoles...',
        choices: pickChoices(DAYS[(today + 1) % 7], [DAYS[(today + 6) % 7], DAYS[(today + 2) % 7]]),
      },
    ];
  }
}
