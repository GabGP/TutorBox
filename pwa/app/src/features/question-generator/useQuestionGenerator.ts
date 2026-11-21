import { useCallback, useRef, useState } from 'react';
import { PROGRESS_ANIMATION } from './generator.constants';
import { GenerationProgress, QuestionGenerationStatus, TopicModel } from './generator.types';
import { generatorApi } from './generatorApi';
import type { QuizModelLifecycle } from './useQuizModelLifecycle';

/** The progress card shown while the quiz model loads, before the batch has begun. */
function modelLoadingProgress(count: number, topic: string, availableTopics: TopicModel[]): GenerationProgress {
  return {
    done: 0,
    total: count,
    failed: 0,
    ids: [],
    eta: PROGRESS_ANIMATION.DEFAULT_QUESTION_ETA_SECONDS,
    currentIndex: 1,
    currentTopic: topic || (availableTopics.length > 0 ? availableTopics[0].name : 'arithmetic'),
    currentSubconcept: null,
    statuses: Array<QuestionGenerationStatus>(count).fill('pending'),
    modelLoading: true,
  };
}

/**
 * Custom React hook for controlling iterative AI question generation.
 * Handles cancellation tokens, progress telemetry tracking, estimated generation time,
 * and batch creation of questions with SymPy verification.
 *
 * `stopGeneration` aborts the in-flight request (the backend stops between
 * attempts and saves nothing) and pauses the loop; `resumeGeneration` asks
 * for the stopped question again and `cancelGeneration` ends the run.
 * A finished run keeps its progress (the result stays on screen) until
 * `clearProgress` is called.
 *
 * With `modelLifecycle`, the run loads the quiz model before its first question and releases
 * it when the run ends, including a cancel. A pause keeps the model loaded.
 *
 * @param {QuizModelLifecycle} [modelLifecycle] - Loads and releases the quiz model around a run.
 * @returns {object} Generation progress status, execution flags, error state, and lifecycle triggers.
 */
export function useQuestionGenerator(modelLifecycle?: QuizModelLifecycle) {
  const [progress, setProgress] = useState<GenerationProgress | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPaused, setIsPaused] = useState(false);
  const tokenRef = useRef<number>(0);
  const inFlightRef = useRef<AbortController | null>(null);
  const settlePauseRef = useRef<((resume: boolean) => void) | null>(null);

  const stopGeneration = useCallback(() => {
    if (!inFlightRef.current) return;
    setIsPaused(true);
    inFlightRef.current.abort();
  }, []);

  const resumeGeneration = useCallback(() => {
    settlePauseRef.current?.(true);
  }, []);

  const cancelGeneration = useCallback(() => {
    tokenRef.current += 1;
    inFlightRef.current?.abort();
    settlePauseRef.current?.(false);
    setIsGenerating(false);
    setIsPaused(false);
    setProgress(null);
  }, []);

  const clearProgress = useCallback(() => {
    setProgress(null);
  }, []);

  /** One batch: its questions in order, until done, cancelled or the token moves on. */
  const runBatch = useCallback(
    async (
      currentToken: number,
      topic: string,
      count: number,
      availableTopics: TopicModel[]
    ): Promise<string[] | null> => {
      // A cancel that arrived while the quiz model was loading ends the run before it starts.
      if (tokenRef.current !== currentToken) return null;

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
        startedAtMs: startTime,
        questionStartedAtMs: startTime,
        finishedAtMs: undefined as number | undefined,
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
        draft.questionStartedAtMs = Date.now();
        publish();

        const request = new AbortController();
        inFlightRef.current = request;
        try {
          const res = await generatorApi.generateQuestion(
            { topic: effectiveTopic, subconcept, save_to_bank: true },
            request.signal
          );
          if (tokenRef.current !== currentToken) return null;
          draft.ids = [...draft.ids, res.question.id];
          statuses[i] = 'success';
        } catch {
          if (tokenRef.current !== currentToken) return null;
          if (request.signal.aborted) {
            // Stopped by the teacher: wait for Reanudar or Cancelar.
            statuses[i] = 'pending';
            publish();
            const resume = await new Promise<boolean>((settle) => {
              settlePauseRef.current = settle;
            });
            settlePauseRef.current = null;
            if (!resume || tokenRef.current !== currentToken) return null;
            setIsPaused(false);
            i--;
            continue;
          }
          draft.failed++;
          statuses[i] = 'failed';
        } finally {
          inFlightRef.current = null;
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

      draft.finishedAtMs = Date.now();
      publish();
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

  const startGeneration = useCallback(
    async (topic: string, count: number, availableTopics: TopicModel[]) => {
      const currentToken = ++tokenRef.current;
      setIsGenerating(true);
      setError(null);
      setProgress(modelLoadingProgress(count, topic, availableTopics));
      await modelLifecycle?.loadForBatch();
      // A cancel during the load left no progress behind: nothing to clear then.
      setProgress((previous) => (previous ? { ...previous, modelLoading: false } : previous));
      try {
        return await runBatch(currentToken, topic, count, availableTopics);
      } finally {
        await modelLifecycle?.releaseAfterBatch();
      }
    },
    [modelLifecycle, runBatch]
  );

  return {
    progress,
    isGenerating,
    isPaused,
    error,
    startGeneration,
    stopGeneration,
    resumeGeneration,
    cancelGeneration,
    clearProgress,
  };
}
