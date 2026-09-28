// Nivel 7 · Calendario Maya y Gregoriano
// CNB Tercero, competencia 7 — 7.7.2 (el Cholq'ij de 13 números, 20 nombres y 260 días, y el
// calendario gregoriano), 7.7.1 (días del mes maya y del mes gregoriano) y 7.7.3 (el Kumatzin
// para contar los días del Cholq'ij). Cada día siguiente se calcula con nextDay, nunca a mano.
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { drawMaya, drawText, inset } from '../shared/draw.js';

const NAWALES = [
  'Imox', "Iq'", "Aq'ab'al", "K'at", 'Kan', 'Keme', 'Kej', "Q'anil", 'Toj', "Tz'i'",
  "B'atz'", 'E', 'Aj', "I'x", "Tz'ikin", 'Ajmaq', "No'j", 'Tijax', 'Kawoq', 'Ajpu',
];
const NUMBERS = 13;
const CHOLQIJ = NUMBERS * NAWALES.length;
const MAYA_MONTH = 20;
const YEAR = 365;
const WEEK = 7;

const nextDay = ([n, i]) => [(n % NUMBERS) + 1, (i + 1) % NAWALES.length];
const dayName = ([n, i]) => `${n} ${NAWALES[i]}`;

// A day of the Cholq'ij: its Maya number and its nawal.
function dayCard(ctx, box, [n, i]) {
  ctx.fillStyle = '#FFF8E1';
  ctx.beginPath(); ctx.roundRect(box.x + box.w * 0.1, box.y + box.h * 0.1, box.w * 0.8, box.h * 0.8, 16); ctx.fill();
  drawMaya(ctx, n, inset({ ...box, w: box.w / 2 }, 0.3, 0.2));
  drawText(ctx, NAWALES[i], inset({ ...box, x: box.x + box.w / 2, w: box.w / 2 }, 0.1, 0.3));
}

export default class CalendariosLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a comparar el calendario maya con el nuestro!'; }
  get colors() { return ['#E1F5FE', '#EFEBE9']; }

  makeRounds() {
    const january = 31;
    const today = [12, NAWALES.indexOf('Kej')];
    const tomorrow = nextDay(today);
    const after = nextDay(tomorrow);
    return [
      {
        say: `Un mes del calendario maya tiene ${MAYA_MONTH} días. Enero tiene ${january} días. ¿Cuántos días más tiene enero?`,
        ask: `${january} días y ${MAYA_MONTH} días: ¿diferencia?`,
        hint: `Resta: ${january} menos ${MAYA_MONTH}.`,
        choices: pickChoices(january - MAYA_MONTH, [january + MAYA_MONTH, 12]),
      },
      {
        say: `El Cholq'ij junta ${NUMBERS} números con ${NAWALES.length} nawales: tiene ${CHOLQIJ} días. Nuestro año tiene ${YEAR}. ¿Cuántos días más tiene nuestro año?`,
        ask: `${YEAR} días y ${CHOLQIJ} días: ¿diferencia?`,
        hint: `Resta: ${YEAR} menos ${CHOLQIJ}.`,
        choices: pickChoices(YEAR - CHOLQIJ, [YEAR + CHOLQIJ, YEAR - CHOLQIJ + 10]),
      },
      {
        say: `Hoy es ${dayName(today)}. Con el Kumatzin contamos los días: el número llega hasta 13 y vuelve a 1. ¿Qué día es pasado mañana?`,
        ask: `Hoy ${dayName(today)}. ¿Pasado mañana?`,
        hint: `Mañana es ${dayName(tomorrow)}. Avanza un día más: el número y el nawal.`,
        scene: (ctx, box) => dayCard(ctx, box, today),
        choices: pickChoices(dayName(after), [`${today[0] + 2} ${NAWALES[after[1]]}`, dayName(tomorrow)]),
      },
      {
        say: `En el Cholq'ij, ¿cada cuántos días se repite el mismo nawal?`,
        ask: '¿Cada cuántos días vuelve un nawal?',
        hint: `Hay ${NAWALES.length} nawales, y pasan uno por día.`,
        choices: pickChoices(NAWALES.length, [NUMBERS, WEEK]),
      },
      {
        say: '¿Y en nuestro calendario, cada cuántos días se repite el lunes?',
        ask: '¿Cada cuántos días vuelve el lunes?',
        hint: 'Una semana tiene lunes, martes, miércoles, jueves, viernes, sábado y domingo.',
        choices: pickChoices(WEEK, [NAWALES.length, 30]),
      },
    ];
  }
}
