import { useCallback, useEffect, useState } from 'react';
import { ApiError } from '../../shared/api/httpClient';
import type { ModelResidency } from '../model-residency/residency.types';
import { NO_NOTICES, type NoticeSink, residencyNotice } from '../model-residency/residencyNotices';
import { ApplianceMode, ModeChange, modeApi } from './modeApi';
import { TUTOR_LOADING_MESSAGE, TUTOR_MODEL_COPY } from './tutorModelNotices';

interface UseApplianceModeOptions {
  pollingIntervalMs?: number;
  enabled?: boolean;
  /** Where the tutor-model toasts go (the teacher view's queue). */
  notices?: NoticeSink;
}

/**
 * Polls the classroom mode so the class screen and student phones follow the teacher's choice.
 * `mode` is null until the first answer; callers treat that as the quiz (the default mode).
 *
 * Switching into tutor mode shows a sticky "loading" toast until the server answers, then the
 * outcome. Leaving tutor mode reports the unload. Other switches stay silent.
 *
 * @param {UseApplianceModeOptions} [options={}] - Polling interval, enable flag and toast sink.
 * @returns {object} Current mode, the mode being saved, the tutor model's last outcome, last error,
 * saving flag and a setter.
 */
export function useApplianceMode({
  pollingIntervalMs = 3000,
  enabled = true,
  notices = NO_NOTICES,
}: UseApplianceModeOptions = {}) {
  const [mode, setModeState] = useState<ApplianceMode | null>(null);
  const [tutorModel, setTutorModel] = useState<ModelResidency | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [pendingMode, setPendingMode] = useState<ApplianceMode | null>(null);

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

  const setMode = useCallback(
    async (next: ApplianceMode): Promise<ModeChange | null> => {
      const enteringTutor = next === 'tutor' && mode !== 'tutor';
      const leavingTutor = mode === 'tutor' && next !== 'tutor';
      const loadingToast = enteringTutor
        ? notices.pushToast({ message: TUTOR_LOADING_MESSAGE, duration: 0 })
        : null;
      setSaving(true);
      setPendingMode(next);
      try {
        const change = await modeApi.setMode(next);
        setModeState(change.mode);
        setTutorModel(change.model);
        setError(null);
        if (enteringTutor || leavingTutor) {
          const notice = residencyNotice(change.model, enteringTutor ? 'load' : 'unload', TUTOR_MODEL_COPY);
          if (notice) notices.pushToast(notice);
        }
        return change;
      } catch (err: unknown) {
        const apiErr = err as ApiError;
        setError(apiErr.detail || apiErr.message);
        return null;
      } finally {
        if (loadingToast) notices.dismissToast(loadingToast);
        setPendingMode(null);
        setSaving(false);
      }
    },
    [mode, notices]
  );

  return { mode, tutorModel, error, saving, pendingMode, setMode };
}
