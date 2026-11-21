import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { generatorApi } from '../generatorApi';
import type { QuizModelLifecycle } from '../useQuizModelLifecycle';
import { useQuestionGenerator } from '../useQuestionGenerator';

vi.mock('../generatorApi', () => ({
  generatorApi: { getMetrics: vi.fn(), generateQuestion: vi.fn() },
}));

/** A generate call that only settles when aborted, like a slow LLM. */
function hangUntilAborted(_payload: unknown, signal?: AbortSignal) {
  return new Promise((_resolve, reject) => {
    signal?.addEventListener('abort', () =>
      reject(new DOMException('The user aborted a request.', 'AbortError'))
    );
  });
}

function answerWith(id: string) {
  return Promise.resolve({ question: { id, question_text: '', options: {} } });
}

/** A lifecycle whose calls are logged in order, to check when the model is loaded and released. */
function recordingLifecycle(log: string[]): QuizModelLifecycle {
  return {
    loadForBatch: vi.fn(async () => {
      log.push('load');
    }),
    releaseAfterBatch: vi.fn(async () => {
      log.push('release');
    }),
  };
}

describe('useQuestionGenerator with a quiz model lifecycle', () => {
  let log: string[];

  beforeEach(() => {
    log = [];
    vi.mocked(generatorApi.getMetrics).mockResolvedValue({
      topic: 'arithmetic',
      total_generated: 0,
      avg_duration_ms: 0,
    });
    vi.mocked(generatorApi.generateQuestion).mockReset();
  });

  it('loads the model before the first question and releases it after the last', async () => {
    vi.mocked(generatorApi.generateQuestion).mockImplementation(() => {
      log.push('generate');
      return answerWith(`q${log.length}`);
    });
    const { result } = renderHook(() => useQuestionGenerator(recordingLifecycle(log)));

    await act(async () => {
      await result.current.startGeneration('arithmetic', 2, []);
    });

    expect(log).toEqual(['load', 'generate', 'generate', 'release']);
  });

  it('keeps the model loaded while the run is paused', async () => {
    vi.mocked(generatorApi.generateQuestion)
      .mockImplementationOnce(hangUntilAborted as typeof generatorApi.generateQuestion)
      .mockImplementationOnce(() => answerWith('q1'));
    const lifecycle = recordingLifecycle(log);
    const { result } = renderHook(() => useQuestionGenerator(lifecycle));

    let run!: Promise<string[] | null>;
    act(() => {
      run = result.current.startGeneration('arithmetic', 1, []);
    });
    await waitFor(() => expect(generatorApi.generateQuestion).toHaveBeenCalledTimes(1));
    act(() => result.current.stopGeneration());
    await waitFor(() => expect(result.current.isPaused).toBe(true));

    expect(lifecycle.releaseAfterBatch).not.toHaveBeenCalled();

    act(() => result.current.resumeGeneration());
    await expect(run).resolves.toEqual(['q1']);
    expect(log).toEqual(['load', 'release']);
  });

  it('releases the model when the paused run is cancelled', async () => {
    vi.mocked(generatorApi.generateQuestion).mockImplementation(
      hangUntilAborted as typeof generatorApi.generateQuestion
    );
    const lifecycle = recordingLifecycle(log);
    const { result } = renderHook(() => useQuestionGenerator(lifecycle));

    let run!: Promise<string[] | null>;
    act(() => {
      run = result.current.startGeneration('arithmetic', 3, []);
    });
    await waitFor(() => expect(generatorApi.generateQuestion).toHaveBeenCalledTimes(1));
    act(() => result.current.stopGeneration());
    await waitFor(() => expect(result.current.isPaused).toBe(true));

    act(() => result.current.cancelGeneration());

    await expect(run).resolves.toBeNull();
    expect(log).toEqual(['load', 'release']);
  });

  it('ends a run cancelled while the model loads before any question is asked', async () => {
    let finishLoad!: () => void;
    const lifecycle: QuizModelLifecycle = {
      loadForBatch: vi.fn(() => new Promise<void>((settle) => (finishLoad = settle))),
      releaseAfterBatch: vi.fn(async () => undefined),
    };
    const { result } = renderHook(() => useQuestionGenerator(lifecycle));

    let run!: Promise<string[] | null>;
    act(() => {
      run = result.current.startGeneration('arithmetic', 2, []);
    });
    act(() => result.current.cancelGeneration());
    await act(async () => finishLoad());

    await expect(run).resolves.toBeNull();
    expect(generatorApi.generateQuestion).not.toHaveBeenCalled();
    expect(lifecycle.releaseAfterBatch).toHaveBeenCalledTimes(1);
    expect(result.current.progress).toBeNull();
  });

  it('releases the model even when no question could be made', async () => {
    vi.mocked(generatorApi.generateQuestion).mockRejectedValue(new Error('HTTP 502'));
    const lifecycle = recordingLifecycle(log);
    const { result } = renderHook(() => useQuestionGenerator(lifecycle));

    await act(async () => {
      await expect(result.current.startGeneration('arithmetic', 1, [])).resolves.toBeNull();
    });

    expect(log).toEqual(['load', 'release']);
    expect(result.current.error).toContain('no respondió');
  });

  it('shows the model-loading card until the model is ready, then the question progress', async () => {
    let finishLoad!: () => void;
    const lifecycle: QuizModelLifecycle = {
      loadForBatch: vi.fn(() => new Promise<void>((settle) => (finishLoad = settle))),
      releaseAfterBatch: vi.fn(async () => undefined),
    };
    vi.mocked(generatorApi.generateQuestion)
      .mockImplementationOnce(() => answerWith('q1'))
      .mockImplementationOnce(() => answerWith('q2'));
    const { result } = renderHook(() => useQuestionGenerator(lifecycle));

    let run!: Promise<string[] | null>;
    act(() => {
      run = result.current.startGeneration('arithmetic', 2, []);
    });
    expect(result.current.progress?.modelLoading).toBe(true);
    expect(result.current.progress?.total).toBe(2);
    expect(generatorApi.generateQuestion).not.toHaveBeenCalled();

    await act(async () => finishLoad());

    await expect(run).resolves.toEqual(['q1', 'q2']);
    expect(result.current.progress?.modelLoading).toBeFalsy();
    expect(result.current.progress?.done).toBe(2);
  });

  it('reports why each failed question failed, and carries on with the next', async () => {
    const { ApiError } = await import('../../../shared/api/httpClient');
    vi.mocked(generatorApi.generateQuestion)
      .mockRejectedValueOnce(new ApiError('Bad Gateway', 502, 'LocalSLM HTTP 500: unexpected EOF'))
      .mockImplementationOnce(() => answerWith('q_two'));
    const failures: string[] = [];
    const { result } = renderHook(() => useQuestionGenerator(undefined, (message) => failures.push(message)));

    let ids: string[] | null = null;
    await act(async () => {
      ids = await result.current.startGeneration('arithmetic', 2, []);
    });

    expect(ids).toEqual(['q_two']);
    expect(failures).toEqual([
      'Pregunta 1: el modelo se quedó sin memoria y el Jetson lo detuvo. Libera memoria en Estado del Jetson y vuelve a intentarlo.',
    ]);
  });
});
