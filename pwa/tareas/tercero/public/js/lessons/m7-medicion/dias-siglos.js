// Nivel 7 · Días, Semanas, Meses y Siglos
// CNB Tercero, competencia 7 — 7.6.3 (equivalencias entre días, semanas, meses, años, décadas y
// siglos) y 7.6.4 (patrones en los días de un mes). Las fechas se calculan con el calendario.
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { drawText, inset } from '../shared/draw.js';

const DAYS_PER_WEEK = 7;
const MONTHS_PER_YEAR = 12;
const YEARS_PER_DECADE = 10;
const DECADES_PER_CENTURY = 10;
const MONTH_DAYS = {
  enero: 31, febrero: 28, marzo: 31, abril: 30, mayo: 31, junio: 30,
  julio: 31, agosto: 31, septiembre: 30, octubre: 31, noviembre: 30, diciembre: 31,
};
const WEEK = ['L', 'M', 'M', 'J', 'V', 'S', 'D'];

/** A month page: `first` is the column of day 1 (0 = lunes); marked days are painted. */
function calendar(ctx, box, { first, days, mark }) {
  const cw = box.w / WEEK.length;
  const rows = Math.ceil((first + days) / WEEK.length) + 1;
  const rh = box.h / rows;
  WEEK.forEach((d, i) => drawText(ctx, d, { x: box.x + cw * i, y: box.y, w: cw, h: rh }, i === 0 ? '#C62828' : '#37474F'));
  for (let day = 1; day <= days; day++) {
    const k = first + day - 1;
    const cell = { x: box.x + (k % WEEK.length) * cw, y: box.y + (Math.floor(k / WEEK.length) + 1) * rh, w: cw, h: rh };
    if (mark.includes(day)) {
      ctx.fillStyle = '#FFE082';
      ctx.fillRect(cell.x + 1, cell.y + 1, cw - 2, rh - 2);
    }
    drawText(ctx, day, inset(cell, 0.12, 0.15));
  }
}

export default class DiasSiglosLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a medir el tiempo en días, meses y siglos!'; }
  get colors() { return ['#E1F5FE', '#FFFDE7']; }

  makeRounds() {
    const weeks = 3;
    const years = 2;
    const century = YEARS_PER_DECADE * DECADES_PER_CENTURY;
    const monday = 3;
    const first = (((0 - (monday - 1)) % DAYS_PER_WEEK) + DAYS_PER_WEEK) % DAYS_PER_WEEK;
    const may = { first, days: MONTH_DAYS.mayo, mark: [monday] };
    const short = Object.keys(MONTH_DAYS).filter((m) => MONTH_DAYS[m] < 30);
    return [
      {
        say: `Una semana tiene ${DAYS_PER_WEEK} días. ¿Cuántos días hay en ${weeks} semanas?`,
        ask: `${weeks} semanas = ¿días?`,
        hint: `Suma ${DAYS_PER_WEEK} días por cada semana.`,
        choices: pickChoices(weeks * DAYS_PER_WEEK, [weeks + DAYS_PER_WEEK, weeks * 10]),
      },
      {
        say: `Un año tiene ${MONTHS_PER_YEAR} meses. ¿Cuántos meses hay en ${years} años?`,
        ask: `${years} años = ¿meses?`,
        hint: `Suma ${MONTHS_PER_YEAR} meses por cada año.`,
        choices: pickChoices(years * MONTHS_PER_YEAR, [years + MONTHS_PER_YEAR, years * 10]),
      },
      {
        say: `Una década tiene ${YEARS_PER_DECADE} años, y un siglo tiene ${DECADES_PER_CENTURY} décadas. ¿Cuántos años tiene un siglo?`,
        ask: '1 siglo = ¿años?',
        hint: `Son ${DECADES_PER_CENTURY} veces ${YEARS_PER_DECADE} años.`,
        choices: pickChoices(century, [YEARS_PER_DECADE, century * 10]),
      },
      {
        say: `En este calendario de mayo, el ${monday} es lunes. ¿Qué fecha es el lunes siguiente?`,
        ask: `Si el ${monday} es lunes, ¿el próximo lunes?`,
        hint: `De un lunes al siguiente pasan ${DAYS_PER_WEEK} días. Baja por la columna del lunes.`,
        scene: (ctx, box) => calendar(ctx, box, may),
        choices: pickChoices(monday + DAYS_PER_WEEK, [monday + 1, monday + DAYS_PER_WEEK + 1]),
      },
      {
        say: `¿Qué fecha es el tercer lunes de mayo?`,
        ask: '¿Cuál es el tercer lunes de mayo?',
        hint: `El primer lunes es el ${monday}. Suma ${DAYS_PER_WEEK} para cada lunes.`,
        scene: (ctx, box) => calendar(ctx, box, may),
        choices: pickChoices(monday + 2 * DAYS_PER_WEEK, [monday + DAYS_PER_WEEK, monday + 3 * DAYS_PER_WEEK]),
      },
      {
        say: '¿Qué mes tiene menos de 30 días?',
        ask: '¿Qué mes tiene menos de 30 días?',
        hint: 'Es el mes más corto del año, el segundo mes.',
        choices: pickChoices(short[0], ['abril', 'junio']),
      },
    ];
  }
}
