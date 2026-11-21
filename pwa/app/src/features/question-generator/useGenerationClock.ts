import { useEffect, useRef, useState } from 'react';
import { PEDAGOGICAL_STAGES, PROGRESS_ANIMATION } from './generator.constants';
import type { GenerationProgress } from './generator.types';

function wholeSecondsBetween(fromMs: number, toMs: number): number {
  return Math.max(0, Math.floor((toMs - fromMs) / 1000));
}

/**
 * Wall-clock state for the generation progress display: rotating pedagogical
 * stage caption, elapsed seconds ticker, and per-question start tracking.
 * Extracted from QuestionGenerationProgress so the view only derives values.
 * `isPaused` freezes the timers but keeps the current question number.
 *
 * The times come from the batch (progress.startedAtMs, questionStartedAtMs, finishedAtMs), so
 * the clock goes on where it was when the card is shown again after a tab switch. A progress
 * without them (an older snapshot) falls back to the time the card mounted.
 */
export function useGenerationClock(
  progress: GenerationProgress,
  isDone: boolean,
  isPaused = false
) {
  const isFrozen = isDone || isPaused;
  const mountedAtRef = useRef(Date.now());
  const batchStartMs = progress.startedAtMs ?? mountedAtRef.current;
  const elapsedUntil = () => wholeSecondsBetween(batchStartMs, progress.finishedAtMs ?? Date.now());

  const [stageIndex, setStageIndex] = useState(0);
  const [elapsedSeconds, setElapsedSeconds] = useState(elapsedUntil);
  const total = progress.total || 1;
  const currentIdx = isDone ? total : (progress.currentIndex ?? Math.min(progress.done + 1, total));
  const prevIdxRef = useRef(currentIdx);
  const fallbackQuestionStartRef = useRef(0);

  useEffect(() => {
    if (isFrozen) return;
    const stageTimer = setInterval(() => {
      setStageIndex((prev) => (prev + 1) % PEDAGOGICAL_STAGES.length);
    }, PROGRESS_ANIMATION.STAGE_SPEED_SECONDS * 1000);
    return () => clearInterval(stageTimer);
  }, [isFrozen]);

  useEffect(() => {
    if (prevIdxRef.current !== currentIdx) {
      prevIdxRef.current = currentIdx;
      fallbackQuestionStartRef.current = wholeSecondsBetween(batchStartMs, Date.now());
    }
  }, [currentIdx, batchStartMs]);

  useEffect(() => {
    setElapsedSeconds(wholeSecondsBetween(batchStartMs, progress.finishedAtMs ?? Date.now()));
    if (isFrozen) return;
    const clock = setInterval(() => {
      setElapsedSeconds(wholeSecondsBetween(batchStartMs, Date.now()));
    }, 1000);
    return () => clearInterval(clock);
  }, [isFrozen, batchStartMs, progress.finishedAtMs]);

  const questionStartSecond =
    progress.questionStartedAtMs !== undefined
      ? wholeSecondsBetween(batchStartMs, progress.questionStartedAtMs)
      : fallbackQuestionStartRef.current;
  return { stageIndex, elapsedSeconds, currentIdx, questionStartSecond };
}
