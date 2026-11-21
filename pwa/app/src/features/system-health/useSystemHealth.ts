import { useEffect, useState } from 'react';
import { toErrorMessage } from '../../shared/lib/errors';
import { systemHealthApi } from './systemHealthApi';
import type { SystemHealthSnapshot } from './systemHealth.types';

/** Pause between two samples while the panel is open and the page is visible. */
export const SYSTEM_HEALTH_POLL_MS = 5000;

const LOAD_ERROR = 'No se pudo leer el estado del Jetson. Se vuelve a intentar.';

/**
 * Samples the appliance while `open` is true: at once, then every poll interval. The next
 * sample is scheduled only after the last answer, so requests never pile up, and a tick
 * while the page is hidden skips the request. Closing (or unmounting) stops the chain and
 * ignores a late answer. A failed sample keeps the last good one and sets `error`.
 * `refresh()` takes a new sample at once and restarts the interval.
 *
 * @param {boolean} open - Whether the panel is showing.
 * @param {number} [pollMs=5000] - Pause between samples (tests shorten it).
 * @returns {{ snapshot: SystemHealthSnapshot | null; error: string | null; refresh: () => void }}
 */
export function useSystemHealth(open: boolean, pollMs = SYSTEM_HEALTH_POLL_MS) {
  const [snapshot, setSnapshot] = useState<SystemHealthSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshCount, setRefreshCount] = useState(0);

  useEffect(() => {
    if (!open) return undefined;
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;

    const sample = async () => {
      if (!document.hidden) {
        try {
          const next = await systemHealthApi.getSnapshot();
          if (!active) return;
          setSnapshot(next);
          setError(null);
        } catch (err) {
          if (active) setError(toErrorMessage(err, LOAD_ERROR));
        }
      }
      if (active) timer = setTimeout(sample, pollMs);
    };

    void sample();
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [open, pollMs, refreshCount]);

  return { snapshot, error, refresh: () => setRefreshCount((count) => count + 1) };
}
