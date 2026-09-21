import { useCallback, useEffect, useState } from 'react';
import { generatorApi } from '../../features/question-generator/generatorApi';
import type { TopicModel } from '../../features/question-generator/generator.types';

/**
 * Shared topic fetcher. Replaces the 4x `getTopics().then(setTopics)` copies
 * in QuestionBankView, QuestionForm, TelemetryView and useTeacherCoordinator.
 */
export function useTopics() {
  const [topics, setTopics] = useState<TopicModel[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await generatorApi.getTopics();
      setTopics(data);
      setError(null);
    } catch {
      // Quiet: topic selectors degrade to empty lists, forms keep typed values.
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { topics, loading, error, refresh };
}
