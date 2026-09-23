// Módulo 7 · Más Alto o Más Bajo
// CNB Primero 1.1.3 (alto-bajo, largo-corto, grande-pequeño) y 7.1.1 (medidas no estándar: la cuarta).
import { ChoiceLesson, numberChoices } from '../shared/choice-lesson.js';
import { drawEmoji } from '../shared/draw.js';

function cornStalk(ctx, box, height) {
  const cx = box.x + box.w / 2;
  const bottom = box.y + box.h;
  const top = bottom - box.h * height;
  ctx.strokeStyle = '#558B2F';
  ctx.lineWidth = 8;
  ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(cx, bottom); ctx.lineTo(cx, top); ctx.stroke();
  ctx.fillStyle = '#7CB342';
  for (let y = bottom - 20, side = 1; y > top + 20; y -= 26, side = -side) {
    ctx.beginPath(); ctx.ellipse(cx + side * 16, y, 18, 5, side * -0.5, 0, Math.PI * 2); ctx.fill();
  }
  ctx.fillStyle = '#FBC02D';
  ctx.beginPath(); ctx.ellipse(cx + 7, top + 18, 6, 14, 0.2, 0, Math.PI * 2); ctx.fill();
}

function snake(ctx, box, length) {
  const y = box.y + box.h / 2;
  const x0 = box.x + (box.w - box.w * length) / 2;
  const x1 = x0 + box.w * length;
  ctx.strokeStyle = '#43A047';
  ctx.lineWidth = 10;
  ctx.lineCap = 'round';
  ctx.beginPath();
  for (let x = x0; x <= x1; x += 2) ctx.lineTo(x, y + Math.sin((x - x0) / 9) * 8);
  ctx.stroke();
  ctx.fillStyle = '#2E7D32';
  ctx.beginPath(); ctx.arc(x1, y + Math.sin((x1 - x0) / 9) * 8, 9, 0, Math.PI * 2); ctx.fill();
}

// The right card is found from the sizes (tallest / shortest / longest), never marked by hand.
function pick(sizes, want, draw) {
  const target = want === 'max' ? Math.max(...sizes) : Math.min(...sizes);
  return sizes.map((s) => ({ correct: s === target, draw: (ctx, box) => draw(ctx, box, s) }));
}

export default class MasAltoBajoLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a comparar y medir!'; }
  get colors() { return ['#E1F5FE', '#DCEDC8']; }

  makeRounds() {
    const cuartas = 4;
    return [
      {
        say: '¿Cuál milpa es la MÁS ALTA?',
        ask: '¿Cuál milpa es la más alta?',
        hint: 'Compara desde abajo: ¿cuál llega más arriba?',
        choices: pick([0.55, 0.95, 0.75], 'max', cornStalk),
      },
      {
        say: '¿Qué niño es el MÁS BAJO?',
        ask: '¿Quién es el más bajo?',
        hint: 'El más bajo es el que llega menos arriba.',
        choices: pick([0.9, 0.5, 0.7], 'min', (ctx, box, s) => {
          const size = box.w * 0.9 * s;
          drawEmoji(ctx, '🧒', box.x + box.w / 2, box.y + box.h - size * 0.5, size);
        }),
      },
      {
        say: '¿Cuál culebra es la MÁS LARGA?',
        ask: '¿Cuál culebra es la más larga?',
        hint: 'Mira de dónde a dónde llega cada culebra.',
        choices: pick([0.5, 0.95, 0.7], 'max', snake),
      },
      {
        say: 'Doña Rosa mide la mesa con su mano, en cuartas. ¿Cuántas cuartas mide la mesa?',
        ask: '¿Cuántas cuartas mide la mesa?',
        hint: 'Cuenta las manos que caben en la mesa.',
        scene: (ctx, box) => {
          const tableY = box.y + box.h * 0.55;
          ctx.fillStyle = '#8D6E63';
          ctx.fillRect(box.x + box.w * 0.06, tableY, box.w * 0.88, box.h * 0.1);
          ctx.fillRect(box.x + box.w * 0.1, tableY, box.w * 0.05, box.h * 0.4);
          ctx.fillRect(box.x + box.w * 0.85, tableY, box.w * 0.05, box.h * 0.4);
          const cell = (box.w * 0.88) / cuartas;
          for (let i = 0; i < cuartas; i++) drawEmoji(ctx, '✋', box.x + box.w * 0.06 + cell * (i + 0.5), tableY - cell * 0.4, cell * 0.75);
        },
        choices: numberChoices(cuartas, { min: 1, max: 8 }),
      },
    ];
  }
}
