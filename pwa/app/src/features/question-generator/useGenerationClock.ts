import { useEffect, useRef, useState } from 'react';
import { PEDAGOGICAL_STAGES, PROGRESS_ANIMATION } from './generator.constants';
import type { GenerationProgress } from './generator.types';

/**
 * Wall-clock state for the generation progress display: rotating pedagogical
 * stage caption, elapsed seconds ticker, and per-question start tracking.
 * Extracted from QuestionGenerationProgress so the view only derives values.
 * `isPaused` freezes the timers but keeps the current question number.
 */
export function useGenerationClock(
  progress: GenerationProgress,
  isDone: boolean,
  isPaused = false
) {
  const isFrozen = isDone || isPaused;
  const [stageIndex, setStageIndex] = useState(0);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const startTimeRef = useRef(Date.now());
  const total = progress.total || 1;
  const currentIdx = isDone ? total : (progress.currentIndex ?? Math.min(progress.done + 1, total));
  const prevIdxRef = useRef(currentIdx);
  const qStartRef = useRef(0);

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
      qStartRef.current = Math.floor((Date.now() - startTimeRef.current) / 1000);
    }
  }, [currentIdx]);

  useEffect(() => {
    if (isFrozen) return;
    const clock = setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - startTimeRef.current) / 1000));
    }, 1000);
    return () => clearInterval(clock);
  }, [isFrozen]);

  return { stageIndex, elapsedSeconds, currentIdx, questionStartSecond: qStartRef.current };
}
