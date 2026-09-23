// Módulo 7 · Los Meses del Año
// CNB Primero, competencia 7 — 7.3.1 (semanas de cada mes y meses del calendario gregoriano)
// y 7.3.2 (eventos tradicionales de la comunidad en el calendario).
import { ChoiceLesson, numberChoices } from '../shared/choice-lesson.js';
import { center } from '../shared/draw.js';

const MONTHS = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
// Rainy season (mayo–octubre) in blue, dry season in orange: how Guatemala lives the year.
const monthColor = (i) => (i >= 4 && i <= 9 ? '#1E88E5' : '#FB8C00');

// Febrero de 2027 starts on a Monday and has 28 days: exactly 4 rows of 7.
const FEB_DAYS = 28;
const WEEK = 7;

function badge(ctx, box, i, star) {
  const { cx, cy } = center(box);
  const r = Math.min(box.w, box.h) * 0.44;
  ctx.fillStyle = monthColor(i);
  ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.fill();
  if (star) {
    ctx.strokeStyle = '#FDD835';
    ctx.lineWidth = 5;
    ctx.stroke();
  }
  ctx.fillStyle = '#FFFFFF';
  ctx.font = `900 ${Math.round(r * 0.95)}px Nunito, sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(String(i + 1), cx, cy + 1);
}

// The twelve months as tappable badges, in two rows of six (fractions of the canvas).
const monthAt = (i) => ({ x: 0.05 + (i % 6) * 0.152, y: 0.16 + Math.floor(i / 6) * 0.17, w: 0.14, h: 0.14 });

// The same two rows of six, drawn inside the picture box; `starred` gets a yellow ring.
function year(ctx, box, starred = -1) {
  const w = box.w / 6;
  MONTHS.forEach((_, i) => {
    const y = box.y + box.h * (0.15 + Math.floor(i / 6) * 0.4);
    badge(ctx, { x: box.x + (i % 6) * w, y, w, h: box.h * 0.35 }, i, i === starred);
  });
}

function february(ctx, box) {
  const cols = WEEK;
  const rows = FEB_DAYS / WEEK;
  const cell = Math.min(box.w / cols, box.h / (rows + 1));
  const x0 = box.x + (box.w - cell * cols) / 2;
  const y0 = box.y + (box.h - cell * (rows + 1)) / 2;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ['L', 'M', 'M', 'J', 'V', 'S', 'D'].forEach((d, c) => {
    ctx.fillStyle = '#5D4037';
    ctx.font = `900 ${Math.round(cell * 0.4)}px Nunito, sans-serif`;
    ctx.fillText(d, x0 + cell * (c + 0.5), y0 + cell * 0.5);
  });
  for (let d = 0; d < FEB_DAYS; d++) {
    const r = Math.floor(d / cols);
    const x = x0 + cell * (d % cols);
    const y = y0 + cell * (r + 1);
    ctx.fillStyle = r % 2 ? '#E3F2FD' : '#FFFFFF';
    ctx.fillRect(x + 2, y + 2, cell - 4, cell - 4);
    ctx.fillStyle = '#1F2A1F';
    ctx.font = `700 ${Math.round(cell * 0.38)}px Nunito, sans-serif`;
    ctx.fillText(String(d + 1), x + cell / 2, y + cell / 2);
  }
}

// Pictures of what we see in each celebration.
function flag(ctx, box) {
  const w = Math.min(box.w, box.h * 1.4) * 0.8;
  const h = w * 0.62;
  const x = box.x + (box.w - w) / 2;
  const y = box.y + (box.h - h) / 2;
  ctx.fillStyle = '#4997D0';
  ctx.fillRect(x, y, w / 3, h);
  ctx.fillRect(x + (w * 2) / 3, y, w / 3, h);
  ctx.fillStyle = '#FFFFFF';
  ctx.fillRect(x + w / 3, y, w / 3, h);
  ctx.strokeStyle = '#90A4AE';
  ctx.lineWidth = 2;
  ctx.strokeRect(x, y, w, h);
}

function kite(ctx, box) {
  const { cx, cy } = center(box);
  const r = Math.min(box.w, box.h) * 0.36;
  const colors = ['#E53935', '#FDD835', '#1E88E5', '#43A047'];
  const pts = [[0, -r], [r * 0.75, 0], [0, r], [-r * 0.75, 0]];
  pts.forEach((p, i) => {
    const q = pts[(i + 1) % 4];
    ctx.fillStyle = colors[i];
    ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + p[0], cy + p[1]); ctx.lineTo(cx + q[0], cy + q[1]); ctx.closePath(); ctx.fill();
  });
  ctx.strokeStyle = '#6D4C41';
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(cx, cy + r);
  for (let i = 1; i <= 4; i++) ctx.lineTo(cx + (i % 2 ? 8 : -8), cy + r + i * 9);
  ctx.stroke();
}

function tree(ctx, box) {
  const { cx } = center(box);
  const h = Math.min(box.h, box.w * 1.3) * 0.8;
  const top = box.y + (box.h - h) / 2;
  ctx.fillStyle = '#2E7D32';
  [0, 1, 2].forEach((i) => {
    const w = h * (0.35 + i * 0.15);
    const y = top + h * (0.12 + i * 0.22);
    ctx.beginPath(); ctx.moveTo(cx, y); ctx.lineTo(cx + w / 2, y + h * 0.3); ctx.lineTo(cx - w / 2, y + h * 0.3); ctx.closePath(); ctx.fill();
  });
  ctx.fillStyle = '#6D4C41';
  ctx.fillRect(cx - h * 0.05, top + h * 0.82, h * 0.1, h * 0.14);
  ctx.fillStyle = '#FDD835';
  ctx.beginPath(); ctx.arc(cx, top + h * 0.1, h * 0.06, 0, Math.PI * 2); ctx.fill();
}

export default class MesesDelAnioLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a conocer el calendario!'; }
  get colors() { return ['#E1F5FE', '#FFF8E1']; }

  makeRounds() {
    const september = MONTHS.indexOf('septiembre');
    const december = MONTHS.indexOf('diciembre');
    return [
      {
        say: `El año tiene estos meses: ${MONTHS.slice(0, -1).join(', ')} y diciembre. ¿Cuántos meses tiene el año?`,
        ask: '¿Cuántos meses tiene el año?',
        hint: 'Cuenta los círculos, del uno hasta el último.',
        scene: (ctx, box) => year(ctx, box),
        choices: numberChoices(MONTHS.length, { max: 15 }),
      },
      {
        say: 'Este es el calendario de febrero. Cada fila es una semana. ¿Cuántas semanas tiene febrero?',
        ask: '¿Cuántas semanas tiene febrero?',
        hint: 'Cuenta las filas de días, de arriba hacia abajo.',
        scene: february,
        choices: numberChoices(FEB_DAYS / WEEK, { min: 1, max: 8 }),
      },
      {
        say: 'El 15 de septiembre celebramos la Independencia de Guatemala. ¿Qué vemos en septiembre?',
        ask: '¿Qué vemos en septiembre?',
        hint: 'En septiembre salen los desfiles con la bandera azul y blanca.',
        scene: (ctx, box) => year(ctx, box, september),
        choices: [
          { correct: true, draw: flag },
          { correct: false, hint: 'Los barriletes gigantes son en noviembre.', draw: kite },
          { correct: false, hint: 'El árbol de Navidad es en diciembre.', draw: tree },
        ],
      },
      {
        say: 'La Navidad es en diciembre, el último mes del año. Toca el mes de diciembre.',
        ask: 'Toca diciembre, el último mes',
        hint: 'Diciembre es el número doce, el último de todos.',
        scene: () => {},
        choices: MONTHS.map((_, i) => ({
          correct: i === december,
          at: monthAt(i),
          draw: (ctx, box) => badge(ctx, box, i, false),
        })),
      },
    ];
  }
}
