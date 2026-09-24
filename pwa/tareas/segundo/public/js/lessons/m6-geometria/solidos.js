// Nivel 6 · Sólidos Geométricos
// CNB Segundo, competencia 6 — 6.1.5 (cono, pirámide, cilindro, prisma rectangular y esfera por
// el número y tipo de caras), 6.1.6 (semejanzas y diferencias) y 6.4.1 (prismas rectangulares:
// cajas). Las respuestas salen de la tabla SOLIDS.
import { ChoiceLesson, numberChoices } from '../shared/choice-lesson.js';
import { center } from '../shared/draw.js';

const FILL = '#FFCC80';
const EDGE = '#6D4C41';

function paint(ctx, path, fill = FILL) {
  ctx.fillStyle = fill;
  ctx.strokeStyle = EDGE;
  ctx.lineWidth = 3;
  ctx.lineJoin = 'round';
  ctx.beginPath(); path(); ctx.fill(); ctx.stroke();
}

function esfera(ctx, cx, cy, r) {
  paint(ctx, () => ctx.arc(cx, cy, r, 0, Math.PI * 2));
  ctx.save();
  ctx.setLineDash([5, 5]);
  ctx.beginPath(); ctx.ellipse(cx, cy, r, r * 0.3, 0, 0, Math.PI); ctx.stroke();
  ctx.restore();
  ctx.fillStyle = 'rgba(255,255,255,0.6)';
  ctx.beginPath(); ctx.ellipse(cx - r * 0.35, cy - r * 0.4, r * 0.2, r * 0.12, -0.6, 0, Math.PI * 2); ctx.fill();
}

function prisma(ctx, cx, cy, r) {
  const [w, h, d] = [r * 1.3, r * 0.9, r * 0.5];
  const [x, y] = [cx - w / 2 - d / 2, cy - h / 2 + d / 2];
  paint(ctx, () => ctx.rect(x, y, w, h));
  paint(ctx, () => { ctx.moveTo(x, y); ctx.lineTo(x + d, y - d); ctx.lineTo(x + w + d, y - d); ctx.lineTo(x + w, y); ctx.closePath(); }, '#FFE0B2');
  paint(ctx, () => { ctx.moveTo(x + w, y); ctx.lineTo(x + w + d, y - d); ctx.lineTo(x + w + d, y + h - d); ctx.lineTo(x + w, y + h); ctx.closePath(); }, '#FFB74D');
}

function cilindro(ctx, cx, cy, r) {
  const [w, h] = [r * 0.8, r * 1.5];
  paint(ctx, () => { ctx.moveTo(cx - w, cy - h / 2); ctx.lineTo(cx - w, cy + h / 2); ctx.ellipse(cx, cy + h / 2, w, w * 0.3, 0, Math.PI, 0, true); ctx.lineTo(cx + w, cy - h / 2); });
  paint(ctx, () => ctx.ellipse(cx, cy - h / 2, w, w * 0.3, 0, 0, Math.PI * 2), '#FFE0B2');
}

function cono(ctx, cx, cy, r) {
  const [w, h] = [r * 0.85, r * 1.6];
  paint(ctx, () => { ctx.moveTo(cx, cy - h / 2); ctx.lineTo(cx - w, cy + h / 2); ctx.ellipse(cx, cy + h / 2, w, w * 0.3, 0, Math.PI, 0, true); ctx.closePath(); });
}

function piramide(ctx, cx, cy, r) {
  const top = [cx, cy - r * 0.9];
  const [fl, fr, br] = [[cx - r * 0.9, cy + r * 0.6], [cx + r * 0.4, cy + r * 0.8], [cx + r * 0.9, cy + r * 0.35]];
  paint(ctx, () => { ctx.moveTo(...top); ctx.lineTo(...fl); ctx.lineTo(...fr); ctx.closePath(); });
  paint(ctx, () => { ctx.moveTo(...top); ctx.lineTo(...fr); ctx.lineTo(...br); ctx.closePath(); }, '#FFB74D');
}

// faces: all faces, flat: flat faces, base: shape of the base.
const SOLIDS = {
  esfera: { draw: esfera, faces: 1, flat: 0, base: null },
  prisma: { draw: prisma, faces: 6, flat: 6, base: 'rectángulo' },
  cilindro: { draw: cilindro, faces: 3, flat: 2, base: 'círculo' },
  cono: { draw: cono, faces: 2, flat: 1, base: 'círculo' },
  piramide: { draw: piramide, faces: 5, flat: 5, base: 'cuadrado' },
};

const solid = (name) => (ctx, box) => {
  const { cx, cy } = center(box);
  SOLIDS[name].draw(ctx, cx, cy, Math.min(box.w, box.h) * 0.4);
};

const pick = (names, test) => names.map((name) => ({ correct: test(name), draw: solid(name) }));

export default class SolidosLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a conocer los sólidos, figuras que se pueden agarrar!'; }
  get colors() { return ['#FFEBEE', '#E3F2FD']; }

  makeRounds() {
    return [
      {
        say: '¿Cuál sólido es redondo como una pelota? Se llama esfera.',
        ask: '¿Cuál es la esfera?',
        hint: 'La esfera es redonda por todos lados y no tiene caras planas.',
        choices: pick(['esfera', 'cilindro', 'cono'], (n) => SOLIDS[n].flat === 0),
      },
      {
        say: '¿Cuál tiene forma de caja? Se llama prisma rectangular.',
        ask: '¿Cuál es el prisma rectangular?',
        hint: 'Una caja tiene caras planas en forma de rectángulo.',
        choices: pick(['prisma', 'piramide', 'cilindro'], (n) => SOLIDS[n].base === 'rectángulo'),
      },
      {
        say: 'Este es un cilindro, como un tambor. ¿Cuántas caras planas tiene?',
        ask: '¿Cuántas caras planas tiene el cilindro?',
        hint: 'Una cara plana arriba y otra abajo. El lado es curvo.',
        scene: solid('cilindro'),
        choices: numberChoices(SOLIDS.cilindro.flat, { max: 9 }),
      },
      {
        say: '¿Cuántas caras tiene una caja, el prisma rectangular?',
        ask: '¿Cuántas caras tiene la caja?',
        hint: 'Arriba, abajo, adelante, atrás, y los dos lados.',
        scene: solid('prisma'),
        choices: numberChoices(SOLIDS.prisma.faces, { max: 9 }),
      },
      {
        say: 'El cono y la pirámide tienen punta. ¿Cuál tiene la base redonda?',
        ask: '¿Cuál tiene la base redonda?',
        hint: 'Mira la parte de abajo. ¿Cuál es un círculo?',
        choices: pick(['cono', 'piramide'], (n) => SOLIDS[n].base === 'círculo'),
      },
    ];
  }
}
