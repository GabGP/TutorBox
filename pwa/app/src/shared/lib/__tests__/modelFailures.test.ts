import { describe, expect, it } from 'vitest';
import { ApiError } from '../../api/httpClient';
import { explainGenerationFailure, explainSpeechFailure } from '../modelFailures';

function badGateway(detail: string): ApiError {
  return new ApiError('Bad Gateway', 502, `Failed to generate valid quiz question: ${detail}`);
}

describe('explainGenerationFailure', () => {
  it.each([
    [
      'SLM completion request failed on attempt 1: LocalSLM HTTP 500: {"error":{"message":"unexpected EOF"}}',
      'Pregunta 2: el modelo se quedó sin memoria y el Jetson lo detuvo. Libera memoria en Estado del Jetson y vuelve a intentarlo.',
    ],
    [
      'SLM completion request failed on attempt 1: LocalSLM request failed: [Errno 111] Connection refused',
      'Pregunta 2: el servidor de modelos no responde; suele estar reiniciándose tras quedarse sin memoria. Espera unos segundos.',
    ],
    [
      'SLM completion request failed on attempt 1: LocalSLM request failed: timed out',
      'Pregunta 2: el modelo tardó demasiado. Pasa cuando no cabe entero en la GPU por falta de memoria. Libera memoria en Estado del Jetson y vuelve a intentarlo.',
    ],
    [
      'Failed to generate a valid quiz question after 3 attempts. Errors: Duplicate option values',
      'Pregunta 2: las respuestas del modelo no pasaron la revisión matemática. Se sigue con la siguiente.',
    ],
    ['something new', 'Pregunta 2: no se pudo crear.'],
  ])('explains %s', (detail, expected) => {
    expect(explainGenerationFailure(badGateway(detail), 2)).toBe(expected);
  });

  it('says when the Jetson cannot be reached at all', () => {
    expect(explainGenerationFailure(new ApiError('offline', 0), 1)).toBe('Pregunta 1: no hay conexión con el Jetson.');
  });

  it('copes with something that is not an error object', () => {
    expect(explainGenerationFailure(undefined, 3)).toBe('Pregunta 3: no se pudo crear.');
  });
});

describe('explainSpeechFailure', () => {
  const noVoice = 'Este aparato no tiene voz instalada (espeak-ng).';

  it('keeps the no-voice wording for a 503', () => {
    expect(explainSpeechFailure(new ApiError('x', 503, 'No engine'), noVoice)).toBe(noVoice);
  });

  it('points to memory when the voice timed out', () => {
    const error = new ApiError('x', 500, 'Qwen synthesis timed out after 10.0s.');
    expect(explainSpeechFailure(error, noVoice)).toBe(
      'La voz no cupo en memoria o tardó demasiado. Elige una voz más ligera (Piper) en Ajustes o libera memoria en Estado del Jetson y vuelve a intentarlo.'
    );
  });

  it('names a lost connection and any other failure', () => {
    expect(explainSpeechFailure(new ApiError('x', 0), noVoice)).toBe('No hay conexión con el Jetson para preparar la voz.');
    expect(explainSpeechFailure(new ApiError('x', 500, 'boom'), noVoice)).toBe(
      'No se pudo preparar la voz. La explicación sigue en la pantalla.'
    );
  });
});
