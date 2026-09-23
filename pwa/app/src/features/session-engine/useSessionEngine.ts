import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError } from '../../shared/api/httpClient';
import { SessionModel } from './session.types';
import { sessionApi } from './sessionApi';

interface UseSessionEngineOptions {
  pollingIntervalMs?: number;
  enabled?: boolean;
  targetSessionId?: string | null;
  fallbackSessionId?: string | null;
}

/**
 * Custom React hook for polling and synchronizing quiz session state.
 * Supports active session polling (`/session/current`), explicit session ID polling,
 * automatic fallback retention for completed sessions, and manual refreshes.
 *
 * @param {UseSessionEngineOptions} [options={}] - Polling interval, enable flag, and target session IDs.
 * @returns {object} Current session snapshot, error state, manual refresh function, and session setter.
 */
export function useSessionEngine({
  pollingIntervalMs = 1000,
  enabled = true,
  targetSessionId,
  fallbackSessionId,
}: UseSessionEngineOptions = {}) {
  const [session, setSession] = useState<SessionModel | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const lastKnownIdRef = useRef<string | null>(targetSessionId || fallbackSessionId || null);

  useEffect(() => {
    if (targetSessionId) {
      lastKnownIdRef.current = targetSessionId;
    }
  }, [targetSessionId]);

  const pollOnce = useCallback(async () => {
    try {
      let data: SessionModel;
      if (targetSessionId) {
        data = await sessionApi.getSessionById(targetSessionId);
      } else {
        data = await sessionApi.getCurrentSession();
      }
      lastKnownIdRef.current = data.id;
      setSession(data);
      setError(null);
      return data;
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      if (apiErr.status === 404 && lastKnownIdRef.current && !targetSessionId) {
        // Completed sessions are omitted from /current: follow fallback ID
        try {
          const fallbackData = await sessionApi.getSessionById(lastKnownIdRef.current);
          setSession(fallbackData);
          setError(null);
          return fallbackData;
        } catch {
          setSession(null);
        }
      } else if (apiErr.status === 404) {
        setSession(null);
      }
      setError(apiErr);
      return null;
    }
  }, [targetSessionId]);

  useEffect(() => {
    if (!enabled) return;

    let mounted = true;
    let timerId: ReturnType<typeof setTimeout>;

    const tick = async () => {
      if (!mounted) return;
      await pollOnce();
      if (mounted) {
        timerId = setTimeout(tick, pollingIntervalMs);
      }
    };

    tick();

    return () => {
      mounted = false;
      clearTimeout(timerId);
    };
  }, [enabled, pollingIntervalMs, pollOnce]);

  return { session, error, refresh: pollOnce, setSession };
}
