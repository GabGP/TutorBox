// Nivel 4 · Sumar y Restar en la Milpa
// CNB Segundo, competencia 4 — 4.8.1 (restas con minuendo de dos dígitos, prestando), 4.7.1
// (sumas de dos dígitos sin llevar) y 4.7.2 (cálculo mental).
// En la resta, el distractor principal es el error de restar el dígito menor al mayor (32 - 7 -> 35).
import { ChoiceLesson, pickChoices } from '../shared/choice-lesson.js';
import { drawBlocks, drawText } from '../shared/draw.js';

/** The classic borrowing mistake: in each column, subtract the smaller digit from the bigger one. */
export function smallFromBig(a, b) {
  return (Math.floor(a / 10) - Math.floor(b / 10)) * 10 + Math.abs((a % 10) - (b % 10));
}

function op(a, sign, b, say, hint, wrongs) {
  const answer = sign === '+' ? a + b : a - b;
  return {
    say,
    ask: `${a} ${sign} ${b} = ?`,
    hint,
    scene: (ctx, box) => {
      drawText(ctx, `${a} ${sign} ${b}`, { x: box.x, y: box.y, w: box.w, h: box.h * 0.28 });
      const body = { x: box.x + box.w * 0.04, y: box.y + box.h * 0.32, w: box.w * 0.44, h: box.h * 0.62 };
      drawBlocks(ctx, a, body);
      if (sign === '+') drawBlocks(ctx, b, { ...body, x: box.x + box.w * 0.52 });
    },
    choices: pickChoices(answer, wrongs ?? (sign === '+' ? [answer + 10, answer - 1] : [smallFromBig(a, b), answer - 1])),
  };
}

export default class SumarRestarLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a sumar y restar elotes de la milpa!'; }
  get colors() { return ['#FFFDE7', '#F1F8E9']; }

  makeRounds() {
    return [
      op(23, '+', 14, 'Don Pedro cosechó 23 elotes y su hijo 14. ¿Cuántos elotes juntaron?', 'Suma primero las unidades: 3 más 4. Después las decenas: 2 más 1.'),
      op(42, '+', 35, 'En la tienda hay 42 bolsas de frijol y llegan 35 más. ¿Cuántas hay ahora?', 'Unidades con unidades y decenas con decenas.'),
      op(30, '+', 40, 'Calcula en tu mente: 30 más 40. ¿Cuánto es?', 'Piensa en decenas: 3 decenas más 4 decenas.', [7, 60]),
      op(32, '−', 7, 'Doña Rosa tenía 32 elotes y vendió 7. ¿Cuántos le quedan?', 'A 2 no le puedes quitar 7. Presta una decena: ahora tienes 12 unidades.'),
      op(45, '−', 18, 'Había 45 tortillas y la familia comió 18. ¿Cuántas quedan?', 'A 5 no le puedes quitar 8. Presta una decena y cambia el 4 por 3.'),
      op(60, '−', 24, 'Juan tenía 60 quetzales y gastó 24. ¿Cuántos le quedan?', 'A 0 no le puedes quitar 4. Presta una decena: 10 menos 4.'),
    ];
  }
}
