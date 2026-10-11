import { useEffect } from 'react';
import { presenceApi } from './presenceApi';

/** How often a waiting phone tells the server it is still in the class. */
export const HEARTBEAT_INTERVAL_MS = 5000;

interface UsePresenceHeartbeatOptions {
  /** The caller decides which phones count as waiting in the class. */
  enabled: boolean;
  intervalMs?: number;
}

/**
 * Keeps this student's phone on the teacher's class list. Beats once when
 * enabled, then every `intervalMs`, and again as soon as the page becomes
 * visible (a phone that was locked or in the background may have stopped its
 * timer). A failed beat is ignored: the next one tries again.
 *
 * @param {UsePresenceHeartbeatOptions} options - `enabled` gate and optional interval for tests.
 */
export function usePresenceHeartbeat({
  enabled,
  intervalMs = HEARTBEAT_INTERVAL_MS,
}: UsePresenceHeartbeatOptions): void {
  useEffect(() => {
    if (!enabled) return undefined;

    const beat = () => {
      void presenceApi.sendHeartbeat().catch(() => undefined);
    };
    const beatWhenVisible = () => {
      if (document.visibilityState === 'visible') beat();
    };

    beat();
    const timer = setInterval(beat, intervalMs);
    document.addEventListener('visibilitychange', beatWhenVisible);
    return () => {
      clearInterval(timer);
      document.removeEventListener('visibilitychange', beatWhenVisible);
    };
  }, [enabled, intervalMs]);
}
