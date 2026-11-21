/**
 * Turns a failed model request (question generation or class voice) into one Spanish sentence for
 * a toast. On the Jetson most of these failures come down to memory: Ollama's model is killed by
 * the kernel when RAM runs out, it restarts and refuses connections for a few seconds, or it runs
 * partly on the CPU and passes the time limit. Each message says what to do, and points to
 * "Liberar memoria" in the Estado del Jetson panel when memory is the likely cause.
 */

const FREE_MEMORY_HINT = 'Libera memoria en Estado del Jetson y vuelve a intentarlo.';

interface FailedRequest {
  status?: number;
  detail?: string;
  message?: string;
}

function reasonText(error: unknown): { status: number | undefined; text: string } {
  const failed = (error ?? {}) as FailedRequest;
  return { status: failed.status, text: `${failed.detail ?? ''} ${failed.message ?? ''}`.toLowerCase() };
}

/**
 * The toast for one question that could not be created.
 *
 * @param {unknown} error - What generatorApi.generateQuestion threw (an ApiError, usually 502).
 * @param {number} questionNumber - 1-based position of the question in the batch.
 * @returns {string} One sentence naming the cause and what to do.
 */
export function explainGenerationFailure(error: unknown, questionNumber: number): string {
  const { status, text } = reasonText(error);
  const prefix = `Pregunta ${questionNumber}:`;
  if (status === 0) return `${prefix} no hay conexión con el Jetson.`;
  if (text.includes('unexpected eof') || text.includes('signal: killed') || text.includes('out of memory')) {
    return `${prefix} el modelo se quedó sin memoria y el Jetson lo detuvo. ${FREE_MEMORY_HINT}`;
  }
  if (text.includes('connection refused') || text.includes('unreachable') || text.includes('remote end closed')) {
    return `${prefix} el servidor de modelos no responde; suele estar reiniciándose tras quedarse sin memoria. Espera unos segundos.`;
  }
  if (text.includes('timed out') || text.includes('timeout')) {
    return `${prefix} el modelo tardó demasiado. Pasa cuando no cabe entero en la GPU por falta de memoria. ${FREE_MEMORY_HINT}`;
  }
  if (text.includes('after') && text.includes('attempts')) {
    return `${prefix} las respuestas del modelo no pasaron la revisión matemática. Se sigue con la siguiente.`;
  }
  return `${prefix} no se pudo crear.`;
}

/**
 * The message for a class voice that could not speak (GET /session/{id}/speech).
 *
 * @param {unknown} error - What speechApi.getSpeechBlobUrl threw.
 * @param {string} noVoiceMessage - The wording for a 503 (no voice installed for this language).
 * @returns {string} One sentence naming the cause and what to do.
 */
export function explainSpeechFailure(error: unknown, noVoiceMessage: string): string {
  const { status, text } = reasonText(error);
  if (status === 503) return noVoiceMessage;
  if (status === 0) return 'No hay conexión con el Jetson para preparar la voz.';
  if (text.includes('timed out') || text.includes('out of memory') || text.includes('memory')) {
    return `La voz no cupo en memoria o tardó demasiado. Elige una voz más ligera (Piper) en Ajustes o ${FREE_MEMORY_HINT.charAt(0).toLowerCase()}${FREE_MEMORY_HINT.slice(1)}`;
  }
  return 'No se pudo preparar la voz. La explicación sigue en la pantalla.';
}
