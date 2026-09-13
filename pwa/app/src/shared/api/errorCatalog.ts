/**
 * Standard Spanish error message dictionary matching legacy tb.js.
 */
export const ERROR_MESSAGES: Record<number, string> = {
  0: 'Sin conexión con TutorBox',
  401: 'Usuario o PIN incorrecto',
  403: 'No tienes permiso para esto',
  404: 'No se encontró',
  409: 'Ya existe',
  422: 'Usuario de 3 a 32 letras o números y PIN de 4 a 8 números',
  429: 'Demasiados intentos, espera un momento',
  502: 'El modelo no respondió',
};

/**
 * Resolves a human-friendly Spanish error description for an HTTP status code,
 * falling back to server response details or a generic error code.
 *
 * @param {number} status - HTTP response status code (e.g. 401, 404, 429).
 * @param {string} [fallbackDetail] - Optional fallback error message from server payload.
 * @returns {string} User-friendly Spanish error string.
 */
export function getErrorMessage(status: number, fallbackDetail?: string): string {
  if (status in ERROR_MESSAGES) {
    return ERROR_MESSAGES[status];
  }
  return fallbackDetail || `Error ${status}`;
}
