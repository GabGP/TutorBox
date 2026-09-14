import { useCallback, useRef, useState } from 'react';
import { GenerationProgress, QuestionGenerationStatus, TopicModel } from './generator.types';
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

      const startTime = Date.now();
      let eta = 12;
      try {
        const metrics = await generatorApi.getMetrics(topic || undefined);
        if (metrics && metrics.avg_duration_ms > 0) {
          eta = Math.max(1, Math.round(metrics.avg_duration_ms / 1000));
        }
      } catch {
        // Fall back to baseline 12s
      }

      const initialTopic =
        topic ||
        (availableTopics.length > 0 ? availableTopics[0].name : 'arithmetic');

      const statuses: QuestionGenerationStatus[] = Array(count).fill('pending');
      if (count > 0) statuses[0] = 'generating';

      const currentProgress: GenerationProgress = {
        done: 0,
        total: count,
        failed: 0,
        ids: [],
        eta,
        currentIndex: 1,
        currentTopic: initialTopic,
        currentSubconcept: null,
        statuses: [...statuses],
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

        statuses[i] = 'generating';
        currentProgress.currentIndex = i + 1;
        currentProgress.currentTopic = effectiveTopic;
        currentProgress.currentSubconcept = subconcept;
        currentProgress.statuses = [...statuses];
        setProgress({ ...currentProgress });

        try {
          const res = await generatorApi.generateQuestion({
            topic: effectiveTopic,
            subconcept,
            save_to_bank: true,
          });
          if (tokenRef.current !== currentToken) return null;
          currentProgress.ids.push(res.question.id);
          statuses[i] = 'success';
        } catch {
          if (tokenRef.current !== currentToken) return null;
          currentProgress.failed++;
          statuses[i] = 'failed';
        }

        currentProgress.done++;
        const elapsedMs = Date.now() - startTime;
        if (currentProgress.done > 0) {
          currentProgress.eta = Math.max(1, Math.round(elapsedMs / (currentProgress.done * 1000)));
        }
        if (i + 1 < count) {
          statuses[i + 1] = 'generating';
        }
        currentProgress.statuses = [...statuses];
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
