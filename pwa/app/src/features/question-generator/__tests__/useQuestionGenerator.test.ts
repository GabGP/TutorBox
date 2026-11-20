import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { generatorApi } from '../generatorApi';
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

describe('useQuestionGenerator stop, resume and cancel', () => {
  beforeEach(() => {
    vi.mocked(generatorApi.getMetrics).mockResolvedValue({
      topic: 'arithmetic',
      total_generated: 0,
      avg_duration_ms: 0,
    });
    vi.mocked(generatorApi.generateQuestion).mockReset();
  });

  it('aborts the request on stop and asks for the same question on resume', async () => {
    vi.mocked(generatorApi.generateQuestion)
      .mockImplementationOnce(hangUntilAborted as typeof generatorApi.generateQuestion)
      .mockImplementationOnce(() => answerWith('q1'));
    const { result } = renderHook(() => useQuestionGenerator());

    let run!: Promise<string[] | null>;
    act(() => {
      run = result.current.startGeneration('arithmetic', 1, []);
    });
    await waitFor(() => expect(generatorApi.generateQuestion).toHaveBeenCalledTimes(1));

    act(() => result.current.stopGeneration());
    const firstSignal = vi.mocked(generatorApi.generateQuestion).mock.calls[0][1];
    expect(firstSignal?.aborted).toBe(true);
    // Paused turns on at once; the question goes back to pending once the
    // aborted request has rejected, a tick later.
    await waitFor(() => expect(result.current.progress?.statuses).toEqual(['pending']));
    expect(result.current.isPaused).toBe(true);
    expect(result.current.isGenerating).toBe(true);

    act(() => result.current.resumeGeneration());

    await expect(run).resolves.toEqual(['q1']);
    expect(generatorApi.generateQuestion).toHaveBeenCalledTimes(2);
    expect(vi.mocked(generatorApi.generateQuestion).mock.calls[1][0]).toEqual(
      vi.mocked(generatorApi.generateQuestion).mock.calls[0][0]
    );
    await waitFor(() => expect(result.current.isGenerating).toBe(false));
    expect(result.current.isPaused).toBe(false);
    expect(result.current.progress?.failed).toBe(0);
  });

  it('ends the run with null when cancelled while stopped', async () => {
    vi.mocked(generatorApi.generateQuestion).mockImplementation(
      hangUntilAborted as typeof generatorApi.generateQuestion
    );
    const { result } = renderHook(() => useQuestionGenerator());

    let run!: Promise<string[] | null>;
    act(() => {
      run = result.current.startGeneration('arithmetic', 3, []);
    });
    await waitFor(() => expect(generatorApi.generateQuestion).toHaveBeenCalledTimes(1));
    act(() => result.current.stopGeneration());
    await waitFor(() => expect(result.current.isPaused).toBe(true));

    act(() => result.current.cancelGeneration());

    await expect(run).resolves.toBeNull();
    expect(generatorApi.generateQuestion).toHaveBeenCalledTimes(1);
    expect(result.current.isGenerating).toBe(false);
    expect(result.current.isPaused).toBe(false);
    expect(result.current.progress).toBeNull();
  });

  it('aborts the in-flight request when cancelled mid-question', async () => {
    vi.mocked(generatorApi.generateQuestion).mockImplementation(
      hangUntilAborted as typeof generatorApi.generateQuestion
    );
    const { result } = renderHook(() => useQuestionGenerator());

    let run!: Promise<string[] | null>;
    act(() => {
      run = result.current.startGeneration('arithmetic', 2, []);
    });
    await waitFor(() => expect(generatorApi.generateQuestion).toHaveBeenCalledTimes(1));

    act(() => result.current.cancelGeneration());

    await expect(run).resolves.toBeNull();
    const signal = vi.mocked(generatorApi.generateQuestion).mock.calls[0][1];
    expect(signal?.aborted).toBe(true);
  });

  it('ignores stop when no request is in flight', () => {
    const { result } = renderHook(() => useQuestionGenerator());
    act(() => result.current.stopGeneration());
    expect(result.current.isPaused).toBe(false);
  });

  it('keeps a finished run on screen until clearProgress', async () => {
    vi.mocked(generatorApi.generateQuestion).mockImplementation(() => answerWith('q1'));
    const { result } = renderHook(() => useQuestionGenerator());

    await act(async () => {
      await result.current.startGeneration('arithmetic', 1, []);
    });
    expect(result.current.progress?.done).toBe(1);

    act(() => result.current.clearProgress());
    expect(result.current.progress).toBeNull();
  });
});
