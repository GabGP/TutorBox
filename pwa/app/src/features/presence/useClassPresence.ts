import { useEffect, useState } from 'react';
import { ApiError } from '../../shared/api/httpClient';
import { presenceApi } from './presenceApi';
import type { ClassPresence } from './presence.types';

/** Pause between polls of the teacher's class list. */
export const CLASS_PRESENCE_POLL_MS = 2000;

const LOAD_ERROR = 'No se pudo cargar la lista de alumnos. Se vuelve a intentar.';

/**
 * Polls the teacher's class list. A failed poll keeps the last good list and
 * sets `error`; the next good poll clears it. Each poll waits for the previous
 * answer before it schedules the next one, so answers never overlap.
 *
 * @param {number} [pollingIntervalMs=2000] - Pause between polls (tests shorten it).
 * @returns {{ presence: ClassPresence | null; error: string | null }} `presence` stays null until the first answer.
 */
export function useClassPresence(pollingIntervalMs = CLASS_PRESENCE_POLL_MS) {
  const [presence, setPresence] = useState<ClassPresence | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;

    const poll = async () => {
      try {
        const next = await presenceApi.getClassPresence();
        if (!active) return;
        setPresence(next);
        setError(null);
      } catch (err) {
        if (active) setError(err instanceof ApiError ? err.message : LOAD_ERROR);
      }
      if (active) timer = setTimeout(poll, pollingIntervalMs);
    };

    void poll();
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [pollingIntervalMs]);

  return { presence, error };
}
