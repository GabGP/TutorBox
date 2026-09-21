/**
 * UI tuning constants for the generation progress display.
 * Split out of generator.types.ts so DTOs and animation tuning evolve independently.
 */

export const PROGRESS_ANIMATION = {
  STAGE_SPEED_SECONDS: 5,
  SHIMMER_SPEED_SECONDS: 5,
  CYCLE_SPEED_SECONDS: 5,
  ORBIT_SPEED_SECONDS: 3.6,
  DEFAULT_QUESTION_ETA_SECONDS: 12,
  MOBILE_PILL_COLS_MAX: 5,
  DESKTOP_PILL_COLS_MAX: 10,
} as const;

export const PEDAGOGICAL_STAGES = [
  'Redactando el enunciado del problema...',
  'Diseñando opciones para dudas frecuentes...',
  'Comprobando la exactitud de los cálculos...',
  'Guardando en el banco del dispositivo...',
] as const;
