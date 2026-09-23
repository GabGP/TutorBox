import { useCallback, useEffect, useState } from 'react';
import { ApiError } from '../../shared/api/httpClient';
import { ApplianceMode, modeApi } from './modeApi';

interface UseApplianceModeOptions {
  pollingIntervalMs?: number;
  enabled?: boolean;
}

/**
 * Polls the classroom mode so the class screen and student phones follow the teacher's choice.
 * `mode` is null until the first answer; callers treat that as the quiz (the default mode).
 *
 * @param {UseApplianceModeOptions} [options={}] - Polling interval and enable flag.
 * @returns {object} Current mode, last error message, saving flag and a setter for staff.
 */
export function useApplianceMode({ pollingIntervalMs = 3000, enabled = true }: UseApplianceModeOptions = {}) {
  const [mode, setModeState] = useState<ApplianceMode | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!enabled) return;
    let mounted = true;
    let timerId: ReturnType<typeof setTimeout>;

    const tick = async () => {
      try {
        const next = await modeApi.getMode();
        if (mounted) setModeState(next);
      } catch {
        // Wi-Fi hiccup: keep the last known mode and ask again on the next tick.
      }
      if (mounted) timerId = setTimeout(tick, pollingIntervalMs);
    };

    tick();
    return () => {
      mounted = false;
      clearTimeout(timerId);
    };
  }, [enabled, pollingIntervalMs]);

  const setMode = useCallback(async (next: ApplianceMode) => {
    setSaving(true);
    try {
      setModeState(await modeApi.setMode(next));
      setError(null);
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      setError(apiErr.detail || apiErr.message);
    } finally {
      setSaving(false);
    }
  }, []);

  return { mode, error, saving, setMode };
}
