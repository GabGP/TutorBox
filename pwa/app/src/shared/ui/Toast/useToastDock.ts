import { useEffect, type RefObject } from 'react';

/** CSS variable the toast viewport rises above (see Toast.module.css). */
const DOCK_VARIABLE = '--toast-dock';

/**
 * Lifts every toast above a bar at the bottom of the screen (the quiz footer,
 * the tutor chat composer): publishes how far the bar's top edge sits from the
 * bottom of the viewport while it is mounted, so a toast never covers it.
 * Re-measures when the bar or the window (an on-screen keyboard) resizes.
 */
export function useToastDock(barRef: RefObject<HTMLElement | null>): void {
  useEffect(() => {
    const bar = barRef.current;
    if (!bar) return;
    const root = document.documentElement;
    const publish = () => {
      const clearance = Math.max(0, window.innerHeight - bar.getBoundingClientRect().top);
      root.style.setProperty(DOCK_VARIABLE, `${Math.round(clearance)}px`);
    };
    publish();
    const observer = typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(publish);
    observer?.observe(bar);
    window.addEventListener('resize', publish);
    return () => {
      observer?.disconnect();
      window.removeEventListener('resize', publish);
      root.style.removeProperty(DOCK_VARIABLE);
    };
  }, [barRef]);
}
