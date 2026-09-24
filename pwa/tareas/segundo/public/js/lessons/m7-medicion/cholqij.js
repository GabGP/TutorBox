// Nivel 7 · El Calendario Cholq'ij
// CNB Segundo, competencia 7 — 7.5.2 (días y meses del calendario maya Cholq'ij), 7.5.3 (el
// Kumatzin para contar los días) y 4.1.4 (fechas con numeración maya).
// Cada día tiene un número del 1 al 13 y uno de 20 nawales; los dos avanzan juntos y, al llegar
// al final, vuelven a empezar. El día siguiente se calcula con nextDay, nunca a mano.
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { drawMaya, drawText, inset } from '../shared/draw.js';

const NAWALES = [
  'Imox', "Iq'", "Aq'ab'al", "K'at", 'Kan', 'Keme', 'Kej', "Q'anil", 'Toj', "Tz'i'",
  "B'atz'", 'E', 'Aj', "I'x", "Tz'ikin", 'Ajmaq', "No'j", 'Tijax', 'Kawoq', 'Ajpu',
];
const NUMBERS = 13;

const nextDay = (n, i) => [(n % NUMBERS) + 1, (i + 1) % NAWALES.length];
const dayName = (n, i) => `${n} ${NAWALES[i]}`;

// A day of the Cholq'ij: its Maya number and its nawal.
function dayCard(ctx, box, n, i) {
  ctx.fillStyle = '#FFF8E1';
  ctx.beginPath(); ctx.roundRect(box.x + box.w * 0.1, box.y + box.h * 0.1, box.w * 0.8, box.h * 0.8, 16); ctx.fill();
  drawMaya(ctx, n, inset({ ...box, w: box.w / 2 }, 0.3, 0.2));
  drawText(ctx, NAWALES[i], inset({ ...box, x: box.x + box.w / 2, w: box.w / 2 }, 0.1, 0.3));
}

// Wrong answers: counting on to 14, or going back a day.
function tomorrowNumber(n, i, say, hint) {
  const [next] = nextDay(n, i);
  return {
    say,
    ask: `Hoy es ${dayName(n, i)}. ¿Qué número sigue?`,
    hint,
    scene: (ctx, box) => dayCard(ctx, box, n, i),
    choices: pickChoices(next, [n + 1, n - 1, n + 2].filter((v) => v !== next).slice(0, 2), { draw: drawMaya }),
  };
}

export default class CholqijLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a contar los días con el calendario maya Cholq\'ij!'; }
  get colors() { return ['#E1F5FE', '#EFEBE9']; }

  makeRounds() {
    const imox = 0;
    const ajpu = NAWALES.length - 1;
    const [, afterAjpu] = nextDay(8, ajpu);
    const [n2, i2] = nextDay(1, imox);
    return [
      {
        say: `El Cholq'ij junta ${NUMBERS} números con ${NAWALES.length} nawales: ${NUMBERS} veces ${NAWALES.length}. ¿Cuántos días tiene?`,
        ask: `${NUMBERS} × ${NAWALES.length} días`,
        hint: 'No es el calendario de 365 días. Son 13 veces 20.',
        scene: (ctx, box) => {
          const w = box.w / 3;
          drawMaya(ctx, NUMBERS, inset({ ...box, w }, 0.2, 0.15));
          drawText(ctx, '×', { x: box.x + w, y: box.y, w, h: box.h });
          drawMaya(ctx, NAWALES.length, inset({ ...box, x: box.x + 2 * w, w }, 0.2, 0.15));
        },
        choices: pickChoices(NUMBERS * NAWALES.length, [NUMBERS + NAWALES.length, 365]),
      },
      tomorrowNumber(5, 10, "Hoy es 5 B'atz'. Mañana el número sube uno. ¿Qué número tiene mañana?", 'Mañana es un número más.'),
      tomorrowNumber(13, 12, 'Hoy es 13 Aj. El Kumatzin, la serpiente, cuenta del 1 al 13 y vuelve a empezar. ¿Qué número tiene mañana?', 'Después del 13 no viene el 14: vuelve el 1.'),
      {
        say: 'Hoy es 1 Imox. Mañana avanzan el número y el nawal. ¿Cuál es el día de mañana?',
        ask: 'Hoy es 1 Imox. ¿Y mañana?',
        hint: "Cambian los dos: el número sube uno y el nawal pasa al siguiente, Iq'.",
        scene: (ctx, box) => dayCard(ctx, box, 1, imox),
        choices: pickChoices(dayName(n2, i2), [dayName(1, i2), dayName(n2, imox)]),
      },
      {
        say: 'Hoy es 8 Ajpu, el último de los 20 nawales. ¿Qué nawal viene mañana?',
        ask: 'Después de Ajpu, ¿qué nawal sigue?',
        hint: 'Los nawales dan la vuelta: después del último vuelve el primero, Imox.',
        scene: (ctx, box) => dayCard(ctx, box, 8, ajpu),
        choices: pickChoices(NAWALES[afterAjpu], [NAWALES[ajpu - 1], NAWALES[ajpu]]),
      },
    ];
  }
}
