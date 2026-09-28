// Nivel 7 · El Reloj en Minutos
// CNB Tercero, competencia 7 — 7.6.1 (lectura del reloj en minutos y horas), 7.6.2 (medir la
// duración de un evento) y 7.6.5 (problemas con unidades de tiempo). Distractores: las agujas al
// revés, leer el número que toca la aguja larga como minutos (3:25 -> 3:05) y 2:70.
import { ChoiceLesson, pickChoices, stacked } from '../shared/choice-lesson.js';
import { center } from '../shared/draw.js';

const label = (h, m) => `${h}:${String(m).padStart(2, '0')}`;
const swapped = (h, m) => [Math.round(m / 5) || 12, (h % 12) * 5];
const later = (h, m, add) => {
  const t = h * 60 + m + add;
  return [Math.floor(t / 60) % 12 || 12, t % 60];
};

function clock(ctx, box, h, m) {
  const { cx, cy } = center(box);
  const r = Math.min(box.w, box.h) * 0.45;
  ctx.save();
  ctx.fillStyle = '#FFFFFF';
  ctx.strokeStyle = '#01579B';
  ctx.lineWidth = Math.max(3, r * 0.07);
  ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
  ctx.strokeStyle = '#37474F';
  for (let i = 0; i < 60; i++) {
    const a = (i * Math.PI) / 30;
    const inner = i % 5 ? r * 0.88 : r * 0.8;
    ctx.lineWidth = i % 5 ? 1 : 2.5;
    ctx.beginPath(); ctx.moveTo(cx + Math.cos(a) * inner, cy + Math.sin(a) * inner); ctx.lineTo(cx + Math.cos(a) * r * 0.93, cy + Math.sin(a) * r * 0.93); ctx.stroke();
  }
  ctx.fillStyle = '#1F2A1F';
  ctx.font = `bold ${Math.round(r * 0.2)}px Nunito, sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  for (let n = 1; n <= 12; n++) {
    const a = (n * Math.PI) / 6 - Math.PI / 2;
    ctx.fillText(String(n), cx + Math.cos(a) * r * 0.66, cy + Math.sin(a) * r * 0.66);
  }
  const hand = (turns, len, width, color) => {
    const a = turns * Math.PI * 2 - Math.PI / 2;
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + Math.cos(a) * len, cy + Math.sin(a) * len); ctx.stroke();
  };
  hand(((h % 12) + m / 60) / 12, r * 0.45, Math.max(4, r * 0.09), '#D32F2F');
  hand(m / 60, r * 0.75, Math.max(3, r * 0.05), '#1F2A1F');
  ctx.fillStyle = '#1F2A1F';
  ctx.beginPath(); ctx.arc(cx, cy, r * 0.05, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}

function read(h, m, words, wrongs) {
  return {
    say: 'La aguja corta y roja marca la hora; la larga, los minutos. Cada rayita es un minuto. ¿Qué hora es?',
    ask: '¿Qué hora marca el reloj?',
    hint: `Cuenta de 5 en 5 con la aguja larga. Es ${words}.`,
    scene: (ctx, box) => clock(ctx, box, h, m),
    choices: pickChoices(label(h, m), wrongs),
  };
}

export default class RelojMinutosLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a leer el reloj minuto a minuto!'; }
  get colors() { return ['#E1F5FE', '#FFF8E1']; }

  makeRounds() {
    const shown = [10, 5];
    const [start, end] = [[8, 0], [8, 45]];
    const minutes = end[0] * 60 + end[1] - (start[0] * 60 + start[1]);
    const [leave, trip] = [[2, 30], 40];
    const [hours, half] = [2, 30];
    return [
      read(3, 25, 'las 3 y 25', [label(...swapped(3, 25)), label(3, 25 / 5)]),
      read(8, 40, 'las 8 y 40, o veinte para las 9', [label(9, 40), label(8, 40 / 5)]),
      {
        say: '¿Qué reloj marca las 10 y 5?',
        ask: '¿Cuál marca las 10:05?',
        hint: 'La aguja larga en el 1 son 5 minutos. La corta, en el 10.',
        choices: stacked([swapped(...shown), shown, [shown[0], 1]].map(([h, m]) => ({
          value: label(h, m),
          correct: h === shown[0] && m === shown[1],
          draw: (ctx, box) => clock(ctx, box, h, m),
        }))),
      },
      {
        say: `La clase empieza a las ${label(...start)} y termina a las ${label(...end)}. ¿Cuántos minutos dura?`,
        ask: `De ${label(...start)} a ${label(...end)}: ¿cuántos minutos?`,
        hint: 'Cuenta los minutos que pasan desde que empieza hasta que termina.',
        choices: pickChoices(minutes, [60 - minutes, 60]),
      },
      {
        say: `El bus sale a las ${label(...leave)} y el viaje dura ${trip} minutos. ¿A qué hora llega?`,
        ask: `${label(...leave)} y ${trip} minutos después`,
        hint: 'Una hora tiene 60 minutos: cuando pasas de 60, cambia la hora.',
        choices: pickChoices(label(...later(...leave, trip)), [label(leave[0], leave[1] + trip), label(leave[0] + 1, trip)]),
      },
      {
        say: `Una hora tiene 60 minutos. ¿Cuántos minutos son ${hours} horas y media?`,
        ask: `${hours} horas y media = ¿minutos?`,
        hint: 'Cada hora son 60 minutos, y media hora son 30.',
        choices: pickChoices(hours * 60 + half, [hours * 100 + half, hours * 60]),
      },
    ];
  }
}
