import type { ResidencyCopy } from '../model-residency/residencyNotices';

/** Sticky while the tutor model loads: the mode switch waits for it. */
export const TUTOR_LOADING_MESSAGE = 'Cargando el modelo del tutor…';

/** Toast wording for the tutor model (mode switches in useApplianceMode). */
export const TUTOR_MODEL_COPY: ResidencyCopy = {
  loaded: (seconds) => `Modelo del tutor cargado (${seconds} s)`,
  unloaded: 'Modelo del tutor descargado de la memoria',
  loadFailed: 'No se pudo cargar el modelo del tutor. El tutor responderá solo con pistas.',
  unloadFailed: 'No se pudo descargar el modelo del tutor de la memoria.',
};
