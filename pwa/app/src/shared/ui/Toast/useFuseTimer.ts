import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * Remaining-time fuse for the toast burn line (SwipeToast port,
 * dependency-free). The CSS bar mirrors the same duration; pausing both
 * together keeps them in sync. Re-arms when `duration` changes;
 * `armed=false` (closing) or `duration<=0` (sticky) clears. A hidden tab
 * auto-pauses like a hover.
 */
export function useFuseTimer(
  duration: number,
  armed: boolean,
  onDone: () => void
): { pauseFuse: () => void; resumeFuse: () => void; fuseHeld: boolean } {
  const [held, setHeld] = useState(false);
  const remaining = useRef(duration);
  const startedAt = useRef(0);
  const timer = useRef<number | undefined>(undefined);
  const paused = useRef(false);
  const armedRef = useRef(armed);
  armedRef.current = armed;
  const done = useRef(onDone);
  done.current = onDone;

  const pauseFuse = useCallback(() => {
    if (paused.current || timer.current === undefined) return;
    paused.current = true;
    setHeld(true);
    window.clearTimeout(timer.current);
    timer.current = undefined;
    remaining.current = Math.max(0, remaining.current - (performance.now() - startedAt.current));
  }, []);

  const resumeFuse = useCallback(() => {
    if (!paused.current || !armedRef.current || remaining.current <= 0) return;
    paused.current = false;
    setHeld(false);
    startedAt.current = performance.now();
    timer.current = window.setTimeout(() => done.current(), remaining.current);
  }, []);

  useEffect(() => {
    remaining.current = duration;
    paused.current = false;
    setHeld(false);
    window.clearTimeout(timer.current);
    timer.current = undefined;
    if (!armed || duration <= 0) return undefined;
    startedAt.current = performance.now();
    timer.current = window.setTimeout(() => done.current(), duration);
    return () => window.clearTimeout(timer.current);
  }, [armed, duration]);

  useEffect(() => {
    const onVisibility = () => {
      if (document.hidden) pauseFuse();
      else resumeFuse();
    };
    document.addEventListener('visibilitychange', onVisibility);
    return () => {
      document.removeEventListener('visibilitychange', onVisibility);
      window.clearTimeout(timer.current);
    };
  }, [pauseFuse, resumeFuse]);

  return { pauseFuse, resumeFuse, fuseHeld: held };
}
