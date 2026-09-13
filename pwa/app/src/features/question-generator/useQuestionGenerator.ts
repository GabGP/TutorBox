import { useCallback, useRef, useState } from 'react';
import { GenerationProgress, TopicModel } from './generator.types';
import { generatorApi } from './generatorApi';

/**
 * Custom React hook for controlling iterative AI question generation.
 * Handles cancellation tokens, progress telemetry tracking, estimated generation time,
 * and batch creation of questions with SymPy verification.
 *
 * @returns {object} Generation progress status, execution flags, error state, and lifecycle triggers.
 */
export function useQuestionGenerator() {
  const [progress, setProgress] = useState<GenerationProgress | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const tokenRef = useRef<number>(0);

  const cancelGeneration = useCallback(() => {
    tokenRef.current += 1;
    setIsGenerating(false);
    setProgress(null);
  }, []);

  const startGeneration = useCallback(
    async (topic: string, count: number, availableTopics: TopicModel[]) => {
      const currentToken = ++tokenRef.current;
      setIsGenerating(true);
      setError(null);

      let eta: number | null = null;
      try {
        const metrics = await generatorApi.getMetrics(topic || undefined);
        eta = metrics.avg_duration_ms
          ? Math.max(1, Math.round(metrics.avg_duration_ms / 1000))
          : null;
      } catch {
        // ETA metric is non-critical
      }

      const currentProgress: GenerationProgress = {
        done: 0,
        total: count,
        failed: 0,
        ids: [],
        eta,
      };
      setProgress({ ...currentProgress });

      for (let i = 0; i < count; i++) {
        if (tokenRef.current !== currentToken) return null;

        const effectiveTopic =
          topic ||
          (availableTopics.length > 0
            ? availableTopics[i % availableTopics.length].name
            : 'arithmetic');

        const foundTopic = availableTopics.find((t) => t.name === effectiveTopic);
        const subconcepts = foundTopic?.subconcepts || [];
        const subconcept = subconcepts.length
          ? subconcepts[i % subconcepts.length].name
          : null;

        try {
          const res = await generatorApi.generateQuestion({
            topic: effectiveTopic,
            subconcept,
            save_to_bank: true,
          });
          if (tokenRef.current !== currentToken) return null;
          currentProgress.ids.push(res.question.id);
        } catch {
          if (tokenRef.current !== currentToken) return null;
          currentProgress.failed++;
        }

        currentProgress.done++;
        setProgress({ ...currentProgress });
      }

      setIsGenerating(false);

      if (currentProgress.ids.length === 0) {
        const msg =
          'El modelo no respondió a ninguna pregunta. Revise que el modelo local esté encendido e intente de nuevo.';
        setError(msg);
        return null;
      }

      return currentProgress.ids;
    },
    []
  );

  return {
    progress,
    isGenerating,
    error,
    startGeneration,
    cancelGeneration,
  };
}
