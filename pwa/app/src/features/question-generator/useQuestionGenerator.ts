import { useCallback, useRef, useState } from 'react';
import { PROGRESS_ANIMATION } from './generator.constants';
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
      let eta: number = PROGRESS_ANIMATION.DEFAULT_QUESTION_ETA_SECONDS;
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

      // Local mutable working state; only immutable snapshots are published
      // so consumers never observe an object that later gets mutated.
      const draft = {
        done: 0,
        total: count,
        failed: 0,
        ids: [] as string[],
        eta,
        currentIndex: 1,
        currentTopic: initialTopic,
        currentSubconcept: null as string | null,
      };
      const publish = () => {
        const snapshot: GenerationProgress = {
          ...draft,
          ids: [...draft.ids],
          statuses: [...statuses],
        };
        setProgress(snapshot);
      };
      publish();

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
        draft.currentIndex = i + 1;
        draft.currentTopic = effectiveTopic;
        draft.currentSubconcept = subconcept;
        publish();

        try {
          const res = await generatorApi.generateQuestion({
            topic: effectiveTopic,
            subconcept,
            save_to_bank: true,
          });
          if (tokenRef.current !== currentToken) return null;
          draft.ids = [...draft.ids, res.question.id];
          statuses[i] = 'success';
        } catch {
          if (tokenRef.current !== currentToken) return null;
          draft.failed++;
          statuses[i] = 'failed';
        }

        draft.done++;
        const elapsedMs = Date.now() - startTime;
        if (draft.done > 0) {
          draft.eta = Math.max(1, Math.round(elapsedMs / (draft.done * 1000)));
        }
        if (i + 1 < count) {
          statuses[i + 1] = 'generating';
        }
        publish();
      }

      setIsGenerating(false);

      if (draft.ids.length === 0) {
        const msg =
          'El modelo no respondió a ninguna pregunta. Revise que el modelo local esté encendido e intente de nuevo.';
        setError(msg);
        return null;
      }

      return draft.ids;
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
