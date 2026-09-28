// Nivel 6 · Perímetro en Centímetros y Metros
// CNB Tercero, competencia 6 — 6.2.1 (cálculo del perímetro de un triángulo, cuadrado y rectángulo
// en centímetros y metros). Distractores: el área en vez del perímetro o sumar solo dos lados.
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { drawText, num } from '../shared/draw.js';

/** Draws the polygon scaled to fit, with each side labelled; points are in the figure's units. */
function figure(ctx, box, pts, labels) {
  const xs = pts.map((p) => p[0]);
  const ys = pts.map((p) => p[1]);
  const [w, h] = [Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)];
  const s = Math.min((box.w * 0.62) / w, (box.h * 0.6) / h);
  const ox = box.x + (box.w - w * s) / 2 - Math.min(...xs) * s;
  const oy = box.y + (box.h - h * s) / 2 - Math.min(...ys) * s;
  const P = ([x, y]) => [ox + x * s, oy + y * s];
  const [mx, my] = P([xs.reduce((a, b) => a + b, 0) / xs.length, ys.reduce((a, b) => a + b, 0) / ys.length]);
  ctx.save();
  ctx.fillStyle = 'rgba(165,214,167,0.7)';
  ctx.strokeStyle = '#2E7D32';
  ctx.lineWidth = 4;
  ctx.beginPath(); pts.forEach((p) => ctx.lineTo(...P(p))); ctx.closePath(); ctx.fill(); ctx.stroke();
  ctx.restore();
  pts.forEach((p, i) => {
    const [ax, ay] = P(p);
    const [bx, by] = P(pts[(i + 1) % pts.length]);
    const [cx, cy] = [(ax + bx) / 2, (ay + by) / 2];
    const d = Math.hypot(cx - mx, cy - my) || 1;
    const [lx, ly] = [cx + ((cx - mx) / d) * 26, cy + ((cy - my) / d) * 20];
    drawText(ctx, labels[i], { x: lx - 45, y: ly - 11, w: 90, h: 22 }, '#1B5E20');
  });
}

// A triangle with base a and sides b (left) and c (right), from the law of cosines.
function triangle(a, b, c) {
  const x = (a * a + b * b - c * c) / (2 * a);
  return [[0, 0], [a, 0], [x, -Math.sqrt(b * b - x * x)]];
}

const measure = (unit) => (ctx, v, box) => drawText(ctx, `${num(v)} ${unit}`, box);

export default class PerimetroLesson extends ChoiceLesson {
  get intro() { return '¡El perímetro es la vuelta completa de una figura!'; }
  get colors() { return ['#FFEBEE', '#E8F5E9']; }

  makeRounds() {
    const [lw, lh] = [12, 8];
    const [a, b, c] = [5, 9, 7];
    const side = 25;
    const around = 20;
    const [tw, th] = [90, 60];
    const rect = (w, h) => [[0, 0], [w, 0], [w, h], [0, h]];
    return [
      {
        say: `Don Pedro cercará su terreno rectangular de ${lw} metros por ${lh} metros. ¿Cuántos metros de cerco necesita?`,
        ask: '¿Cuánto mide el perímetro?',
        hint: 'Suma los cuatro lados: los dos largos y los dos cortos.',
        scene: (ctx, box) => figure(ctx, box, rect(lw, lh), [lw, lh, lw, lh].map((v) => `${v} m`)),
        choices: pickChoices(2 * (lw + lh), [lw * lh, lw + lh], { draw: measure('m') }),
      },
      {
        say: 'Este triángulo tiene lados de diferente tamaño. ¿Cuánto mide su perímetro?',
        ask: '¿Cuánto mide el perímetro?',
        hint: 'Suma los tres lados.',
        scene: (ctx, box) => figure(ctx, box, triangle(a, b, c), [a, c, b].map((v) => `${v} cm`)),
        choices: pickChoices(a + b + c, [a + b, a + b + c + 1], { draw: measure('cm') }),
      },
      {
        say: `La cancha de la escuela es un cuadrado de ${side} metros de lado. ¿Cuánto mide la vuelta completa?`,
        ask: '¿Cuánto mide el perímetro?',
        hint: 'El cuadrado tiene 4 lados iguales.',
        scene: (ctx, box) => figure(ctx, box, rect(side, side), Array(4).fill(`${side} m`)),
        choices: pickChoices(4 * side, [2 * side, side * side], { draw: measure('m') }),
      },
      {
        say: `El perímetro de un cuadrado es ${around} centímetros. ¿Cuánto mide cada lado?`,
        ask: `Perímetro ${around} cm. ¿Y cada lado?`,
        hint: 'El cuadrado tiene 4 lados iguales. Reparte el perímetro entre 4.',
        scene: (ctx, box) => figure(ctx, box, rect(1, 1), Array(4).fill('? cm')),
        choices: pickChoices(around / 4, [around / 2, around * 4], { draw: measure('cm') }),
      },
      {
        say: `Doña Rosa pondrá cinta alrededor de un mantel de ${tw} por ${th} centímetros. ¿Cuánta cinta necesita?`,
        ask: '¿Cuántos centímetros de cinta?',
        hint: 'Suma los cuatro lados. Cada 100 centímetros son un metro.',
        scene: (ctx, box) => figure(ctx, box, rect(tw, th), [tw, th, tw, th].map((v) => `${v} cm`)),
        choices: pickChoices(2 * (tw + th), [tw + th, tw * th], { draw: measure('cm') }),
      },
    ];
  }
}
