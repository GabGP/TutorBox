import { useCallback, useEffect, useRef, useState } from 'react';
import type { ToastExitReason } from './toast.types';

/** Non-instant exits play the drop over this portion of slideMs. */
const EXIT_PORTION = 0.7;
/** Extra beat so the drop lands before removal. */
const EXIT_LAG_MS = 60;

export interface ToastExitOptions {
  slideMs?: number;
  toastId: string;
  dismissible?: boolean;
  isDragging: () => boolean;
  holdFuse: () => void;
  releaseFuse: () => void;
  onExit: (id: string, reason: ToastExitReason) => void;
}

export interface ToastExit {
  phase: 'open' | 'closing';
  leaving: boolean;
  instant: boolean;
  exitDelay: number;
  /** Request dismissal; queued when mid-drag, instant for keyboard Esc. */
  close: (why: ToastExitReason) => void;
  /** Reopen a closing toast (pointer down mid-exit). */
  rescue: () => void;
  /** Commit a swipe-out fling (fuse already held by the drag). */
  commitSwipe: () => void;
  /** Run a close that was queued mid-drag (call on release). */
  consumePending: () => void;
  markPointer: () => void;
  markKeyboard: () => void;
}

/**
 * Dismissal state machine (SwipeToast port): open → closing → removed.
 * Close requests mid-drag wait for release; keyboard Esc/action/close
 * skip the drop animation. Swipe commits fling straight out.
 */
export function useToastExit({
  slideMs = 400,
  toastId,
  dismissible = true,
  isDragging,
  holdFuse,
  releaseFuse,
  onExit,
}: ToastExitOptions): ToastExit {
  const [phase, setPhase] = useState<'open' | 'closing'>('open');
  const [leaving, setLeaving] = useState(false);
  const [instant, setInstant] = useState(false);
  const pendingClose = useRef<ToastExitReason | null>(null);
  const lastInput = useRef<'pointer' | 'keyboard'>('pointer');
  const exitTimer = useRef<number | undefined>(undefined);
  const phaseRef = useRef(phase);
  phaseRef.current = phase;
  const leavingRef = useRef(leaving);
  leavingRef.current = leaving;
  const latest = useRef({ onExit, slideMs, toastId });
  latest.current = { onExit, slideMs, toastId };
  const exitDelay = slideMs * EXIT_PORTION + EXIT_LAG_MS;

  const finish = useCallback((why: ToastExitReason, now: boolean) => {
    window.clearTimeout(exitTimer.current);
    exitTimer.current = window.setTimeout(
      () => latest.current.onExit(latest.current.toastId, why),
      now ? 0 : latest.current.slideMs * EXIT_PORTION + EXIT_LAG_MS
    );
  }, []);

  const close = useCallback(
    (why: ToastExitReason) => {
      if (phaseRef.current !== 'open' || leavingRef.current) return;
      if (isDragging()) {
        pendingClose.current = why;
        return;
      }
      holdFuse();
      const now =
        why === 'escape' ||
        ((why === 'action' || why === 'close') && lastInput.current === 'keyboard');
      setInstant(now);
      phaseRef.current = 'closing';
      setPhase('closing');
      finish(why, now);
    },
    [finish, holdFuse, isDragging]
  );
  const closeRef = useRef(close);
  closeRef.current = close;

  const rescue = useCallback(() => {
    window.clearTimeout(exitTimer.current);
    setInstant(false);
    phaseRef.current = 'open';
    setPhase('open');
    releaseFuse();
  }, [releaseFuse]);

  const commitSwipe = useCallback(() => {
    pendingClose.current = null;
    leavingRef.current = true;
    setLeaving(true);
    finish('swipe', false);
  }, [finish]);

  const consumePending = useCallback(() => {
    const queued = pendingClose.current;
    pendingClose.current = null;
    if (queued) closeRef.current(queued);
  }, []);

  useEffect(() => {
    if (!dismissible) return undefined;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') closeRef.current('escape');
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [dismissible]);

  useEffect(() => () => window.clearTimeout(exitTimer.current), []);

  return {
    phase,
    leaving,
    instant,
    exitDelay,
    close,
    rescue,
    commitSwipe,
    consumePending,
    markPointer: () => {
      lastInput.current = 'pointer';
    },
    markKeyboard: () => {
      lastInput.current = 'keyboard';
    },
  };
}
