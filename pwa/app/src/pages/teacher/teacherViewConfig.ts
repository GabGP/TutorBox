/**
 * UI title and action button label configurations for the teacher console view.
 */

export const TEACHER_STEP_TITLES: Record<string, [string, string]> = {
  login: ['TutorBox', 'Iniciar sesión'],
  pin: ['TutorBox', 'PIN nuevo'],
  topic: ['Paso 1 de 3', 'Elegir tema'],
  count: ['Paso 2 de 3', 'Número de preguntas'],
  lobby: ['Paso 3 de 3', 'Preparar el juego'],
  question: ['En juego', 'Respuestas en vivo'],
  reveal: ['En juego', 'Resultado de la pregunta'],
  stats: ['Juego terminado', 'Resumen del grupo'],
};

export const SECONDARY_ACTION_LABELS: Record<string, string> = {
  topic: 'Salir',
  lobby: 'Cancelar',
  stats: 'Inicio',
};

/**
 * Computes the dynamic Spanish button label for the main progression CTA button in the teacher view.
 *
 * @param {string} step - Active teacher step ('topic', 'count', 'lobby', 'question', 'reveal', 'stats').
 * @param {boolean} isGenerating - Whether background AI question generation is actively running.
 * @param {boolean} isClosed - Whether the current question round voting window has closed.
 * @param {boolean} isLastRound - Whether the active round is the final question of the session.
 * @returns {string} The computed Spanish button text.
 */
export function getPrimaryActionLabel(
  step: string,
  isGenerating: boolean,
  isClosed: boolean,
  isLastRound: boolean
): string {
  switch (step) {
    case 'topic':
      return 'Continuar';
    case 'count':
      return 'Crear las preguntas';
    case 'lobby':
      return isGenerating ? 'Creando preguntas…' : 'Comenzar el juego';
    case 'question':
      return isClosed ? 'Ver resultado' : 'Terminar la pregunta';
    case 'reveal':
      return isLastRound ? 'Ver resultados' : 'Siguiente pregunta';
    case 'stats':
      return 'Nuevo juego';
    default:
      return '';
  }
}
