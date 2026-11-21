import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { generatorApi } from '../../../features/question-generator/generatorApi';
import { useTeacherCoordinator } from '../useTeacherCoordinator';

vi.mock('../../../features/question-generator/generatorApi', () => ({
  generatorApi: { getMetrics: vi.fn(), generateQuestion: vi.fn(), loadQuizModel: vi.fn(), unloadQuizModel: vi.fn() },
}));
vi.mock('../../../shared/taxonomy/useTopics', () => ({
  useTopics: () => ({ topics: [] }),
}));
vi.mock('../../../features/speech/useTTSLifecycle', () => ({
  useTTSLifecycle: () => ({ preloadIfUnloaded: vi.fn(), unloadIfLoaded: vi.fn() }),
}));

describe('useTeacherCoordinator question batches and the quiz model', () => {
  it('loads the quiz model for the batch and tells the teacher when it is released', async () => {
    vi.mocked(generatorApi.getMetrics).mockResolvedValue({ topic: 'arithmetic', total_generated: 0, avg_duration_ms: 0 });
    vi.mocked(generatorApi.generateQuestion).mockResolvedValue({
      question: { id: 'q_one', question_text: '', options: {} },
    });
    vi.mocked(generatorApi.loadQuizModel).mockResolvedValue({
      model: 'qwen2.5:3b', action: 'loaded', duration_ms: 3200, detail: null,
    });
    vi.mocked(generatorApi.unloadQuizModel).mockResolvedValue({
      model: 'qwen2.5:3b', action: 'unloaded', duration_ms: null, detail: null,
    });
    const pushToast = vi.fn(() => 'toast');
    const dismissToast = vi.fn();
    const { result } = renderHook(() =>
      useTeacherCoordinator(null, { enabled: false, notices: { pushToast, dismissToast } })
    );
    act(() => result.current.setCount(1));

    let ids: string[] | null = null;
    await act(async () => {
      ids = await result.current.generateIntoBank();
    });

    expect(ids).toEqual(['q_one']);
    expect(pushToast).toHaveBeenCalledWith({ message: 'Cargando el modelo de preguntas…', duration: 0 });
    expect(pushToast).toHaveBeenCalledWith({ message: 'Modelo de preguntas cargado (3,2 s)', tone: 'success' });
    expect(pushToast).toHaveBeenCalledWith({ message: 'Modelo de preguntas descargado de la memoria', tone: 'success' });
    expect(result.current.bankIds).toEqual(['q_one']);
  });
});
