import { useCallback, useEffect, useMemo, useRef } from 'react';
import type { ModelResidency } from '../model-residency/residency.types';
import { type NoticeSink, residencyNotice } from '../model-residency/residencyNotices';
import type { ResidencyCopy } from '../model-residency/residencyNotices';
import { generatorApi } from './generatorApi';

/** Sticky while the quiz model loads; the batch waits for it. */
export const QUIZ_LOADING_MESSAGE = 'Cargando el modelo de preguntas…';

/** Toast wording for the quiz model. */
export const QUIZ_MODEL_COPY: ResidencyCopy = {
  loaded: (seconds) => `Modelo de preguntas cargado (${seconds} s)`,
  unloaded: 'Modelo de preguntas descargado de la memoria',
  loadFailed: 'No se pudo cargar el modelo de preguntas. La generación lo intentará de nuevo.',
  unloadFailed: 'No se pudo descargar el modelo de preguntas de la memoria.',
};

/** What a batch needs: the model loaded before its first question, released after its last. */
export interface QuizModelLifecycle {
  loadForBatch: () => Promise<void>;
  releaseAfterBatch: () => Promise<void>;
}

/**
 * Loads the quiz model when a question batch starts and unloads it when the batch ends, is
 * cancelled, or is abandoned by leaving the page. A failed load warns but never blocks the batch:
 * the backend also loads the model on the first question.
 *
 * @param {NoticeSink} notices - Toast queue for the loading and result messages.
 * @returns {QuizModelLifecycle} Stable `loadForBatch` and `releaseAfterBatch` callbacks.
 */
export function useQuizModelLifecycle({ pushToast, dismissToast }: NoticeSink): QuizModelLifecycle {
  const batchHoldsModelRef = useRef(false);

  const loadForBatch = useCallback(async () => {
    batchHoldsModelRef.current = true;
    const loadingToast = pushToast({ message: QUIZ_LOADING_MESSAGE, duration: 0 });
    const result = await settle(() => generatorApi.loadQuizModel());
    dismissToast(loadingToast);
    const notice = residencyNotice(result, 'load', QUIZ_MODEL_COPY);
    if (notice) pushToast(notice);
  }, [pushToast, dismissToast]);

  const releaseAfterBatch = useCallback(async () => {
    if (!batchHoldsModelRef.current) return;
    batchHoldsModelRef.current = false;
    const result = await settle(() => generatorApi.unloadQuizModel());
    const notice = residencyNotice(result, 'unload', QUIZ_MODEL_COPY);
    if (notice) pushToast(notice);
  }, [pushToast]);

  // Leaving the page mid-batch: the backend's idle countdown would unload the model anyway;
  // this only does it sooner. Nobody is left to read a toast, so none is shown.
  useEffect(
    () => () => {
      if (!batchHoldsModelRef.current) return;
      batchHoldsModelRef.current = false;
      void settle(() => generatorApi.unloadQuizModel());
    },
    []
  );

  return useMemo(() => ({ loadForBatch, releaseAfterBatch }), [loadForBatch, releaseAfterBatch]);
}

/** The server's answer, or null when the request itself failed (network, server down). */
async function settle(request: () => Promise<ModelResidency>): Promise<ModelResidency | null> {
  try {
    return await request();
  } catch {
    return null;
  }
}
