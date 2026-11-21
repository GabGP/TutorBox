import { describe, expect, it, vi } from 'vitest';
import type { ModelResidency } from '../residency.types';
import { NO_NOTICES, residencyNotice, type ResidencyCopy } from '../residencyNotices';

const COPY: ResidencyCopy = {
  loaded: (seconds) => `cargado (${seconds} s)`,
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

describe('NO_NOTICES', () => {
  it('accepts toasts and drops them', () => {
    const dismiss = vi.fn();
    const sink = { ...NO_NOTICES, dismissToast: dismiss };
    expect(NO_NOTICES.pushToast({ message: 'x' })).toBe('');
    sink.dismissToast('');
    expect(dismiss).toHaveBeenCalledWith('');
  });
});
