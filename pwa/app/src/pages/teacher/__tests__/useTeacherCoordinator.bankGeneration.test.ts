import { act, renderHook, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { generatorApi } from '../../../features/question-generator/generatorApi';
import { useTeacherCoordinator } from '../useTeacherCoordinator';

vi.mock('../../../features/question-generator/generatorApi', () => ({
  generatorApi: {
    getMetrics: vi.fn(),
    generateQuestion: vi.fn(),
    loadQuizModel: vi.fn().mockResolvedValue({ action: 'disabled' }),
    unloadQuizModel: vi.fn().mockResolvedValue({ action: 'disabled' }),
  },
}));
vi.mock('../../../shared/taxonomy/useTopics', () => ({
  useTopics: () => ({ topics: [] }),
}));
vi.mock('../../../features/speech/useLobbyVoice', () => ({
  useLobbyVoice: () => ({ prepare: vi.fn(), release: vi.fn() }),
}));

/** A generate call that only settles when aborted, like a slow model. */
function hangUntilAborted(_payload: unknown, signal?: AbortSignal) {
  return new Promise<never>((_resolve, reject) => {
    signal?.addEventListener('abort', () =>
      reject(new DOMException('The user aborted a request.', 'AbortError'))
    );
  });
}

describe('useTeacherCoordinator bank generation', () => {
  it('keeps the questions already saved chosen when Cancelar follows Detener', async () => {
    vi.mocked(generatorApi.getMetrics).mockResolvedValue({
      topic: 'arithmetic',
      total_generated: 0,
      avg_duration_ms: 0,
    });
    vi.mocked(generatorApi.generateQuestion)
      .mockResolvedValueOnce({ question: { id: 'q_saved', question_text: '', options: {} } })
      .mockImplementation(hangUntilAborted);
    const { result } = renderHook(() => useTeacherCoordinator(null, { enabled: false }));
    act(() => result.current.setCount(3));

    let run!: Promise<string[] | null>;
    act(() => {
      run = result.current.generateIntoBank();
    });
    await waitFor(() => expect(generatorApi.generateQuestion).toHaveBeenCalledTimes(2));
    act(() => result.current.stopGeneration());
    await waitFor(() => expect(result.current.isGenerationPaused).toBe(true));

    act(() => result.current.cancelBankGeneration());

    await expect(run).resolves.toBeNull();
    expect(result.current.bankIds).toEqual(['q_saved']);
    expect(result.current.isGenerating).toBe(false);
  });
});
