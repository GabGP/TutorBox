import React, { useCallback, useEffect, useRef, useState } from 'react';

// SwipeToast physics: 3px dead zone, rubberband upward overscroll, flick dismiss.
const DEAD_ZONE = 3;
const RESIST_PX = 24;
const FLICK = 0.11;

type Sample = [number, number];
type DragSession = { id: number; startY: number; grab: number | null; moved: boolean; hist: Sample[] };

const rubberband = (over: number, dim: number, c = 0.55): number =>
  (over * dim * c) / (dim + c * Math.abs(over));

const velocityOf = (hist: Sample[]): number => {
  if (hist.length < 2) return 0;
  const [t0, y0] = hist[0];
  const [t1, y1] = hist[hist.length - 1];
  return performance.now() - t1 > 100 ? 0 : (y1 - y0) / Math.max(1, t1 - t0);
};

type PointerHandler = (e: React.PointerEvent) => void;

export interface SwipeDismissOptions {
  /** Slow-drag distance before release dismisses. A flick always does. */
  swipeDistance?: number;
  /** Snap-back overshoot after an abandoned swipe. 0 stops dead. */
  settleBounce?: number;
  disabled?: boolean;
  /** Fired once the release commits to a swipe-out. */
  onSwipe: (velocity: number) => void;
  /** Fired on every release that does not dismiss (resume fuse, pending close). */
  onDragEnd?: () => void;
}

export interface SwipeDismiss {
  dragY: number;
  swiping: boolean;
  snapStyle: React.CSSProperties | undefined;
  resetSwipe: () => void;
  isDragging: () => boolean;
  bindSwipe: Record<'onPointerDown' | 'onPointerMove' | 'onPointerUp' | 'onPointerCancel', PointerHandler>;
}

/** Vertical swipe-to-dismiss: downward-only, buttons never start a session. */
export function useSwipeDismiss({
  swipeDistance = 40,
  settleBounce = 0.2,
  disabled = false,
  onSwipe,
  onDragEnd,
}: SwipeDismissOptions): SwipeDismiss {
  const [dragY, setDragY] = useState(0);
  const [swiping, setSwiping] = useState(false);
  const [snapping, setSnapping] = useState(false);
  const drag = useRef<DragSession | null>(null);
  const snapTimer = useRef<number | undefined>(undefined);
  const reduce =
    typeof window !== 'undefined' &&
    typeof window.matchMedia === 'function' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  useEffect(() => () => window.clearTimeout(snapTimer.current), []);

  const onPointerDown: PointerHandler = useCallback(
    (e) => {
      if (e.button !== 0 || disabled || drag.current) return;
      if ((e.target as HTMLElement).closest?.('button')) return;
      setSnapping(false);
      drag.current = { id: e.pointerId, startY: e.clientY, grab: null, moved: false, hist: [[performance.now(), 0]] };
    },
    [disabled]
  );

  const onPointerMove: PointerHandler = useCallback((e) => {
    const d = drag.current;
    if (!d || d.id !== e.pointerId) return;
    if (d.grab === null) {
      if (Math.abs(e.clientY - d.startY) < DEAD_ZONE) return;
      d.grab = e.clientY;
      setSwiping(true);
    }
    const raw = e.clientY - d.grab;
    const next = raw >= 0 ? raw : rubberband(raw, RESIST_PX);
    setDragY(next);
    d.moved = true;
    d.hist.push([performance.now(), next]);
    if (d.hist.length > 4) d.hist.shift();
  }, []);

  const endDrag: PointerHandler = useCallback(
    (e) => {
      const d = drag.current;
      if (!d || d.id !== e.pointerId) return;
      drag.current = null;
      setSwiping(false);
      const v = velocityOf(d.hist);
      if (dragY > 0 && (v > FLICK || (dragY >= swipeDistance && v >= 0))) {
        onSwipe(v);
        return;
      }
      if (d.moved) {
        setDragY(0);
        setSnapping(true);
        window.clearTimeout(snapTimer.current);
        snapTimer.current = window.setTimeout(() => setSnapping(false), 550);
      }
      onDragEnd?.();
    },
    [dragY, swipeDistance, onSwipe, onDragEnd]
  );

  const resetSwipe = useCallback(() => {
    drag.current = null;
    setSwiping(false);
    setSnapping(false);
    setDragY(0);
  }, []);

  const isDragging = useCallback(() => drag.current !== null, []);

  const snapStyle: React.CSSProperties | undefined = snapping
    ? reduce
      ? { transition: 'transform 0.2s ease-out' }
      : { transition: `transform 0.5s cubic-bezier(0.3, ${1 + settleBounce * 2}, 0.4, 1)` }
    : undefined;

  return { dragY, swiping, snapStyle, resetSwipe, isDragging, bindSwipe: { onPointerDown, onPointerMove, onPointerUp: endDrag, onPointerCancel: endDrag } };
}
