import { describe, expect, it, vi } from 'vitest';
import type { ModelResidency } from '../residency.types';
import { NO_NOTICES, residencyNotice, type ResidencyCopy } from '../residencyNotices';
import { TUTOR_MODEL_COPY } from '../../mode/tutorModelNotices';
import { QUIZ_MODEL_COPY } from '../../question-generator/useQuizModelLifecycle';

const COPY: ResidencyCopy = {
  loaded: (seconds) => `cargado (${seconds} s)`,
  partialGpu: (seconds, percent) => `cargado (${seconds} s), ${percent} % en la GPU`,
  unloaded: 'descargado',
  loadFailed: 'no cargó',
  unloadFailed: 'no descargó',
};

function answer(action: ModelResidency['action'], durationMs: number | null = null): ModelResidency {
  return { model: 'qwen2.5:3b', action, duration_ms: durationMs, detail: null };
}

describe('residencyNotice', () => {
  it('confirms a load with its time in seconds, in Spanish decimals', () => {
    expect(residencyNotice(answer('loaded', 3200), 'load', COPY)).toEqual({
      message: 'cargado (3,2 s)',
      tone: 'success',
    });
  });

  it('warns when only part of the model fits on the GPU', () => {
    const partial = { ...answer('loaded', 3200), gpu_percent: 65 };
    expect(residencyNotice(partial, 'load', COPY)).toEqual({
      message: 'cargado (3,2 s), 65 % en la GPU',
      tone: 'warn',
    });
  });

  it('confirms a load that fits entirely on the GPU, or whose placement is unknown', () => {
    for (const gpuPercent of [100, null]) {
      const result = { ...answer('loaded', 3200), gpu_percent: gpuPercent };
      expect(residencyNotice(result, 'load', COPY)?.tone).toBe('success');
    }
  });

  it('confirms an unload without a time', () => {
    expect(residencyNotice(answer('unloaded'), 'unload', COPY)).toEqual({
      message: 'descargado',
      tone: 'success',
    });
  });

  it('warns with the wording of the direction that failed', () => {
    expect(residencyNotice(answer('failed'), 'load', COPY)).toEqual({ message: 'no cargó', tone: 'warn' });
    expect(residencyNotice(answer('failed'), 'unload', COPY)).toEqual({ message: 'no descargó', tone: 'warn' });
  });

  it('warns when the request itself failed (no answer at all)', () => {
    expect(residencyNotice(null, 'load', COPY)).toEqual({ message: 'no cargó', tone: 'warn' });
    expect(residencyNotice(null, 'unload', COPY)).toEqual({ message: 'no descargó', tone: 'warn' });
  });

  it.each(['kept', 'unsupported', 'disabled'] as const)('says nothing for %s', (action) => {
    expect(residencyNotice(answer(action), 'load', COPY)).toBeNull();
    expect(residencyNotice(answer(action), 'unload', COPY)).toBeNull();
  });
});

describe('partial-GPU wording', () => {
  it('names the share and the slowdown for each model', () => {
    expect(QUIZ_MODEL_COPY.partialGpu('15,0', 65)).toBe(
      'Modelo de preguntas cargado (15,0 s), pero solo el 65 % cabe en la GPU: las preguntas tardarán mucho más.'
    );
    expect(TUTOR_MODEL_COPY.partialGpu('5,8', 80)).toBe(
      'Modelo del tutor cargado (5,8 s), pero solo el 80 % cabe en la GPU: el tutor responderá más lento.'
    );
  });
});

describe('NO_NOTICES', () => {
  it('accepts toasts and drops them', () => {
    const dismiss = vi.fn();
    const sink = { ...NO_NOTICES, dismissToast: dismiss };
    expect(NO_NOTICES.pushToast({ message: 'x' })).toBe('');
    sink.dismissToast('');
    expect(dismiss).toHaveBeenCalledWith('');
  });
});
