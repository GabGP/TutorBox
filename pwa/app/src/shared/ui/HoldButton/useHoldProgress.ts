import { useCallback, useEffect, useRef, useState } from 'react';
import type { HoldButtonPhase } from './holdButton.types';

interface HoldProgressOptions {
  holdTime: number;
  releaseTime: number;
  resetAfter: number;
  disabled: boolean;
  onHold?: () => void;
  onTap?: () => void;
  onPhaseChange?: (phase: HoldButtonPhase) => void;
}

const TAP_LIMIT_MS = 250;

/**
 * RequestAnimationFrame hold timer.
 * Fills 0→1 linearly over holdTime, snaps back over releaseTime,
 * fires onHold once on completion and onTap on quick releases.
 */
export function useHoldProgress({
  holdTime,
  releaseTime,
  resetAfter,
  disabled,
  onHold,
  onTap,
  onPhaseChange,
}: HoldProgressOptions) {
  const [phase, setPhase] = useState<HoldButtonPhase>('idle');
  const [progress, setProgress] = useState(0);
  const frame = useRef(0);
  const resetTimer = useRef<number | undefined>(undefined);
  const holdStart = useRef(0);
  const pressStart = useRef(0);
  const progressRef = useRef(0);
  const phaseRef = useRef<HoldButtonPhase>('idle');
  const callbacks = useRef({ onHold, onTap, onPhaseChange });
  callbacks.current = { onHold, onTap, onPhaseChange };

  const setPhaseBoth = useCallback((next: HoldButtonPhase) => {
    phaseRef.current = next;
    setPhase(next);
    callbacks.current.onPhaseChange?.(next);
  }, []);

  const setProgressBoth = useCallback((next: number) => {
    progressRef.current = next;
    setProgress(next);
  }, []);

  const cancelFrame = useCallback(() => {
    cancelAnimationFrame(frame.current);
    frame.current = 0;
  }, []);

  const animateBack = useCallback(() => {
    const from = progressRef.current;
    if (from <= 0 || releaseTime <= 0) {
      setProgressBoth(0);
      return;
    }
    const begin = performance.now();
    const tick = (now: number) => {
      const elapsed = now - begin;
      const next = Math.max(0, from * (1 - elapsed / releaseTime));
      setProgressBoth(next);
      if (next > 0) frame.current = requestAnimationFrame(tick);
    };
    frame.current = requestAnimationFrame(tick);
  }, [releaseTime, setProgressBoth]);

  const complete = useCallback(() => {
    cancelFrame();
    setProgressBoth(1);
    setPhaseBoth('done');
    callbacks.current.onHold?.();
    window.clearTimeout(resetTimer.current);
    if (resetAfter > 0) {
      resetTimer.current = window.setTimeout(() => {
        setProgressBoth(0);
        setPhaseBoth('idle');
      }, resetAfter);
    }
  }, [cancelFrame, resetAfter, setPhaseBoth, setProgressBoth]);

  const start = useCallback(() => {
    if (disabled || phaseRef.current === 'done') return;
    if (phaseRef.current === 'holding') return;
    window.clearTimeout(resetTimer.current);
    cancelFrame();
    pressStart.current = performance.now();
    holdStart.current = performance.now() - progressRef.current * holdTime;
    setPhaseBoth('holding');
    const tick = (now: number) => {
      const next = Math.min(1, (now - holdStart.current) / holdTime);
      setProgressBoth(next);
      if (next >= 1) complete();
      else frame.current = requestAnimationFrame(tick);
    };
    frame.current = requestAnimationFrame(tick);
  }, [complete, cancelFrame, disabled, holdTime, setPhaseBoth, setProgressBoth]);

  const release = useCallback(() => {
    if (phaseRef.current !== 'holding') return;
    const pressDuration = performance.now() - pressStart.current;
    cancelFrame();
    const wasTap = pressDuration < TAP_LIMIT_MS && progressRef.current < 1;
    setPhaseBoth('idle');
    animateBack();
    if (wasTap) callbacks.current.onTap?.();
  }, [animateBack, cancelFrame, setPhaseBoth]);

  useEffect(
    () => () => {
      cancelFrame();
      window.clearTimeout(resetTimer.current);
    },
    [cancelFrame]
  );

  return { phase, progress, start, release };
}
