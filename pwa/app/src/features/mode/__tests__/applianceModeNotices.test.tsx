import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '../../../shared/api/httpClient';
import type { ModelResidency } from '../../model-residency/residency.types';
import { modeApi } from '../modeApi';
import { useApplianceMode } from '../useApplianceMode';

afterEach(() => vi.restoreAllMocks());

const TUTOR_LOADING = { message: 'Cargando el modelo del tutor…', duration: 0 };

function model(action: ModelResidency['action'], durationMs: number | null = null): ModelResidency {
  return {
    model: 'hf.co/bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF:Q8_0',
    action,
    duration_ms: durationMs,
    detail: null,
  };
}

function makeSink() {
  let issued = 0;
  return { pushToast: vi.fn(() => `toast-${++issued}`), dismissToast: vi.fn() };
}

describe('useApplianceMode tutor-model notices', () => {
  it('shows the loading toast at once, then the load time, when the switch enters tutor mode', async () => {
    vi.spyOn(modeApi, 'setMode').mockResolvedValue({ mode: 'tutor', model: model('loaded', 3200) });
    const sink = makeSink();
    const { result } = renderHook(() => useApplianceMode({ enabled: false, notices: sink }));

    await act(() => result.current.setMode('tutor'));

    expect(sink.pushToast).toHaveBeenNthCalledWith(1, TUTOR_LOADING);
    expect(sink.dismissToast).toHaveBeenCalledWith('toast-1');
    expect(sink.pushToast).toHaveBeenLastCalledWith({
      message: 'Modelo del tutor cargado (3,2 s)',
      tone: 'success',
    });
    expect(result.current.mode).toBe('tutor');
    expect(result.current.tutorModel?.action).toBe('loaded');
  });

  it('reports the unload when the switch leaves tutor mode, with no loading toast', async () => {
    vi.spyOn(modeApi, 'setMode')
      .mockResolvedValueOnce({ mode: 'tutor', model: model('loaded', 900) })
      .mockResolvedValueOnce({ mode: 'apps', model: model('unloaded') });
    const sink = makeSink();
    const { result } = renderHook(() => useApplianceMode({ enabled: false, notices: sink }));
    await act(() => result.current.setMode('tutor'));
    sink.pushToast.mockClear();

    await act(() => result.current.setMode('apps'));

    expect(sink.pushToast).toHaveBeenCalledTimes(1);
    expect(sink.pushToast).toHaveBeenCalledWith({
      message: 'Modelo del tutor descargado de la memoria',
      tone: 'success',
    });
    expect(result.current.mode).toBe('apps');
  });

  it('stays silent between quiz and take-home mode', async () => {
    vi.spyOn(modeApi, 'setMode').mockResolvedValue({ mode: 'apps', model: model('unloaded') });
    const sink = makeSink();
    const { result } = renderHook(() => useApplianceMode({ enabled: false, notices: sink }));

    await act(() => result.current.setMode('apps'));

    expect(sink.pushToast).not.toHaveBeenCalled();
    expect(sink.dismissToast).not.toHaveBeenCalled();
  });

  it('stays silent when the tutor is picked again while it is already on', async () => {
    vi.spyOn(modeApi, 'setMode').mockResolvedValue({ mode: 'tutor', model: model('loaded', 100) });
    const sink = makeSink();
    const { result } = renderHook(() => useApplianceMode({ enabled: false, notices: sink }));
    await act(() => result.current.setMode('tutor'));
    sink.pushToast.mockClear();
    sink.dismissToast.mockClear();

    await act(() => result.current.setMode('tutor'));

    expect(sink.pushToast).not.toHaveBeenCalled();
    expect(sink.dismissToast).not.toHaveBeenCalled();
  });

  it('warns that the tutor will answer with hints only when its model did not load', async () => {
    vi.spyOn(modeApi, 'setMode').mockResolvedValue({ mode: 'tutor', model: model('failed') });
    const sink = makeSink();
    const { result } = renderHook(() => useApplianceMode({ enabled: false, notices: sink }));

    await act(() => result.current.setMode('tutor'));

    expect(sink.pushToast).toHaveBeenLastCalledWith({
      message: 'No se pudo cargar el modelo del tutor. El tutor responderá solo con pistas.',
      tone: 'warn',
    });
  });

  it('warns when the model could not be unloaded on leaving tutor mode', async () => {
    vi.spyOn(modeApi, 'setMode')
      .mockResolvedValueOnce({ mode: 'tutor', model: model('loaded', 100) })
      .mockResolvedValueOnce({ mode: 'quiz', model: model('failed') });
    const sink = makeSink();
    const { result } = renderHook(() => useApplianceMode({ enabled: false, notices: sink }));
    await act(() => result.current.setMode('tutor'));

    await act(() => result.current.setMode('quiz'));

    expect(sink.pushToast).toHaveBeenLastCalledWith({
      message: 'No se pudo descargar el modelo del tutor de la memoria.',
      tone: 'warn',
    });
  });

  it('drops the loading toast and returns null when the server refuses the switch', async () => {
    vi.spyOn(modeApi, 'setMode').mockRejectedValue(
      new ApiError('Conflicto', 409, 'Termina el juego antes de cambiar de modo.')
    );
    const sink = makeSink();
    const { result } = renderHook(() => useApplianceMode({ enabled: false, notices: sink }));

    let change: unknown;
    await act(async () => {
      change = await result.current.setMode('tutor');
    });

    expect(change).toBeNull();
    expect(sink.dismissToast).toHaveBeenCalledWith('toast-1');
    expect(sink.pushToast).toHaveBeenCalledTimes(1); // the loading toast only
    expect(result.current.error).toBe('Termina el juego antes de cambiar de modo.');
    expect(result.current.mode).toBeNull();
  });
});
