// Nivel 1 · Secuencias con Reglas
// CNB Tercero, competencia 1 — 1.3.1 (expresión de patrones en forma de secuencias de suma, resta
// o multiplicación). Los distractores son reglas equivocadas: sumar la primera diferencia cuando la
// regla es multiplicar, o subir cuando la secuencia baja.
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { drawText } from '../shared/draw.js';

// Each rule knows how to apply itself and which answers a child gets by misreading it.
const RULE = {
  suma: (k) => ({ apply: (n) => n + k, label: `+${k}`, words: `sumar ${k}`, mistakes: (z) => [z + k + 1, z + 2 * k] }),
  resta: (k) => ({ apply: (n) => n - k, label: `−${k}`, words: `restar ${k}`, mistakes: (z) => [z + k, z - 2 * k] }),
  por: (k) => ({ apply: (n) => n * k, label: `×${k}`, words: `multiplicar por ${k}`, mistakes: (z, y) => [z + (z - y), z + k] }),
};

function sequence(start, rule, length = 4) {
  const seq = [start];
  while (seq.length < length) seq.push(rule.apply(seq[seq.length - 1]));
  return seq;
}

/** Number cards in a row; `null` is the blinking gap to fill. */
export function cards(ctx, box, items, t) {
  const w = box.w / items.length;
  items.forEach((n, i) => {
    const b = { x: box.x + w * i + 3, y: box.y + box.h * 0.3, w: w - 6, h: box.h * 0.4 };
    ctx.save();
    ctx.fillStyle = n === null ? `rgba(255,255,255,${0.5 + Math.sin(t * 4) * 0.2})` : '#FFFFFF';
    ctx.beginPath(); ctx.roundRect(b.x, b.y, b.w, b.h, 10); ctx.fill();
    ctx.restore();
    drawText(ctx, n === null ? '?' : n, b, n === null ? '#EF6C00' : '#1F2A1F');
  });
}

function next(start, rule) {
  const seq = sequence(start, rule);
  const [y, z] = seq.slice(-2);
  return {
    say: `Mira la secuencia: ${seq.join(', ')}. Descubre la regla. ¿Qué número sigue?`,
    ask: `${seq.join(', ')}, ¿?`,
    hint: `La regla es ${rule.words}. Hazlo con el último número.`,
    scene: (ctx, box, t) => cards(ctx, box, [...seq, null], t),
    choices: pickChoices(rule.apply(z), rule.mistakes(z, y)),
  };
}

function whichRule(start, rule, others) {
  const seq = sequence(start, rule);
  return {
    say: `Mira: ${seq.join(', ')}. ¿Cuál es la regla de esta secuencia?`,
    ask: '¿Cuál es la regla?',
    hint: 'Compara cada número con el siguiente. ¿Cambia siempre lo mismo, o cada vez más?',
    scene: (ctx, box, t) => cards(ctx, box, seq, t),
    choices: pickChoices(rule.label, others.map((r) => r.label)),
  };
}

export default class SecuenciasLesson extends ChoiceLesson {
  get intro() { return '¡Cada secuencia esconde una regla!'; }
  get colors() { return ['#F3E5F5', '#FFF8E1']; }

  makeRounds() {
    return [
      next(7, RULE.suma(4)),
      next(60, RULE.resta(5)),
      next(3, RULE.por(2)),
      whichRule(5, RULE.por(2), [RULE.suma(5), RULE.suma(10)]),
      whichRule(90, RULE.resta(10), [RULE.suma(10), RULE.resta(20)]),
    ];
  }
}
