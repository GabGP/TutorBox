/**
 * Shared bank question fixture for the question-bank suites.
 * Single source so the split files never drift apart.
 */
export const question = {
  id: 'q1',
  topic: 'sumas',
  subconcept: 'llevar',
  question_text: '¿Cuánto es 27 + 15?',
  options: { A: '32', B: '42', C: '41', D: '43' },
  correct_option: 'B',
  distractors: {
    A: { misconception: 'no-lleva', explanation: 'Olvidó la llevada' },
    C: { misconception: 'resta', explanation: 'Restó en vez de sumar' },
    D: { misconception: 'conteo', explanation: 'Contó de más' },
  },
};
