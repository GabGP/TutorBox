import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { ModelResidency } from '../../model-residency/residency.types';
import { generatorApi } from '../generatorApi';
import { QUIZ_LOADING_MESSAGE, useQuizModelLifecycle } from '../useQuizModelLifecycle';

vi.mock('../generatorApi', () => ({
  generatorApi: { loadQuizModel: vi.fn(), unloadQuizModel: vi.fn() },
}));

function answer(action: ModelResidency['action'], durationMs: number | null = null): ModelResidency {
  return { model: 'qwen2.5:3b', action, duration_ms: durationMs, detail: null };
}

function makeSink() {
  let issued = 0;
  return {
    pushToast: vi.fn(() => `toast-${++issued}`),
    dismissToast: vi.fn(),
  };
}

afterEach(() => vi.restoreAllMocks());

describe('useQuizModelLifecycle loading', () => {
  it('shows a loading toast, then the load time, when the batch starts', async () => {
    vi.mocked(generatorApi.loadQuizModel).mockResolvedValue(answer('loaded', 3200));
    const sink = makeSink();
    const { result } = renderHook(() => useQuizModelLifecycle(sink));

    await act(() => result.current.loadForBatch());

    expect(sink.pushToast).toHaveBeenNthCalledWith(1, { message: QUIZ_LOADING_MESSAGE, duration: 0 });
    expect(sink.dismissToast).toHaveBeenCalledWith('toast-1');
    expect(sink.pushToast).toHaveBeenLastCalledWith({
      message: 'Modelo de preguntas cargado (3,2 s)',
      tone: 'success',
    });
  });

  it('warns when the server could not load the model, and the batch goes on', async () => {
    vi.mocked(generatorApi.loadQuizModel).mockResolvedValue(answer('failed'));
    const sink = makeSink();
    const { result } = renderHook(() => useQuizModelLifecycle(sink));

    await act(() => result.current.loadForBatch());

    expect(sink.pushToast).toHaveBeenLastCalledWith({
      message: 'No se pudo cargar el modelo de preguntas. La generación lo intentará de nuevo.',
      tone: 'warn',
    });
  });

  it('warns when the request itself fails', async () => {
    vi.mocked(generatorApi.loadQuizModel).mockRejectedValue(new Error('offline'));
    const sink = makeSink();
    const { result } = renderHook(() => useQuizModelLifecycle(sink));

    await act(() => result.current.loadForBatch());

    expect(sink.pushToast).toHaveBeenLastCalledWith(expect.objectContaining({ tone: 'warn' }));
  });

  it('stays quiet when the server does not manage the model', async () => {
    vi.mocked(generatorApi.loadQuizModel).mockResolvedValue(answer('disabled'));
    const sink = makeSink();
    const { result } = renderHook(() => useQuizModelLifecycle(sink));

    await act(() => result.current.loadForBatch());

    expect(sink.pushToast).toHaveBeenCalledTimes(1); // only the loading toast
    expect(sink.dismissToast).toHaveBeenCalledWith('toast-1');
  });
});

describe('useQuizModelLifecycle release', () => {
  it('unloads the model after a batch and says so', async () => {
    vi.mocked(generatorApi.loadQuizModel).mockResolvedValue(answer('loaded', 1000));
    vi.mocked(generatorApi.unloadQuizModel).mockResolvedValue(answer('unloaded'));
    const sink = makeSink();
    const { result } = renderHook(() => useQuizModelLifecycle(sink));
    await act(() => result.current.loadForBatch());

    await act(() => result.current.releaseAfterBatch());

    expect(generatorApi.unloadQuizModel).toHaveBeenCalledTimes(1);
    expect(sink.pushToast).toHaveBeenLastCalledWith({
      message: 'Modelo de preguntas descargado de la memoria',
      tone: 'success',
    });
  });

  it('does nothing when no batch loaded the model', async () => {
    const sink = makeSink();
    const { result } = renderHook(() => useQuizModelLifecycle(sink));

    await act(() => result.current.releaseAfterBatch());

    expect(generatorApi.unloadQuizModel).not.toHaveBeenCalled();
    expect(sink.pushToast).not.toHaveBeenCalled();
  });

  it('does not unload twice for one batch', async () => {
    vi.mocked(generatorApi.loadQuizModel).mockResolvedValue(answer('loaded', 1000));
    vi.mocked(generatorApi.unloadQuizModel).mockResolvedValue(answer('unloaded'));
    const { result } = renderHook(() => useQuizModelLifecycle(makeSink()));
    await act(() => result.current.loadForBatch());

    await act(async () => {
      await result.current.releaseAfterBatch();
      await result.current.releaseAfterBatch();
    });

    expect(generatorApi.unloadQuizModel).toHaveBeenCalledTimes(1);
  });

  it('warns when the unload fails', async () => {
    vi.mocked(generatorApi.loadQuizModel).mockResolvedValue(answer('loaded', 1000));
    vi.mocked(generatorApi.unloadQuizModel).mockRejectedValue(new Error('HTTP 500'));
    const sink = makeSink();
    const { result } = renderHook(() => useQuizModelLifecycle(sink));
    await act(() => result.current.loadForBatch());

    await act(() => result.current.releaseAfterBatch());

    expect(sink.pushToast).toHaveBeenLastCalledWith({
      message: 'No se pudo descargar el modelo de preguntas de la memoria.',
      tone: 'warn',
    });
  });

  it('unloads best effort when the page is left mid-batch, without a toast', async () => {
    vi.mocked(generatorApi.loadQuizModel).mockResolvedValue(answer('loaded', 1000));
    vi.mocked(generatorApi.unloadQuizModel).mockRejectedValue(new Error('gone'));
    const sink = makeSink();
    const { result, unmount } = renderHook(() => useQuizModelLifecycle(sink));
    await act(() => result.current.loadForBatch());
    const toastsBeforeLeaving = sink.pushToast.mock.calls.length;

    unmount();

    expect(generatorApi.unloadQuizModel).toHaveBeenCalledTimes(1);
    expect(sink.pushToast).toHaveBeenCalledTimes(toastsBeforeLeaving);
  });

  it('leaves the model alone when the page is left between batches', async () => {
    const { unmount } = renderHook(() => useQuizModelLifecycle(makeSink()));

    unmount();

    expect(generatorApi.unloadQuizModel).not.toHaveBeenCalled();
  });

  it('keeps the same callbacks across renders', () => {
    const sink = makeSink();
    const { result, rerender } = renderHook(() => useQuizModelLifecycle(sink));
    const first = result.current;

    rerender();

    expect(result.current).toBe(first);
  });
});
