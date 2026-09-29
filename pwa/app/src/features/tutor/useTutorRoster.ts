import { useEffect, useState } from 'react';
import { ApiError } from '../../shared/api/httpClient';
import { tutorApi, type TutorStudent } from './tutorApi';

/**
 * Polls the students using the tutor, for the teacher's tutor-mode panel.
 *
 * @param {number} [pollingIntervalMs=4000] - Refresh period.
 * @returns {{ students: TutorStudent[]; loaded: boolean; error: string | null }}
 */
export function useTutorRoster(pollingIntervalMs = 4000) {
  const [students, setStudents] = useState<TutorStudent[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const refresh = async () => {
      try {
        const next = await tutorApi.students();
        if (!active) return;
        setStudents(next);
        setError(null);
      } catch (err) {
        if (active) setError(err instanceof ApiError ? err.message : 'No se pudo cargar la lista.');
      } finally {
        if (active) setLoaded(true);
      }
    };
    void refresh();
    const timer = setInterval(refresh, pollingIntervalMs);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [pollingIntervalMs]);

  return { students, loaded, error };
}
