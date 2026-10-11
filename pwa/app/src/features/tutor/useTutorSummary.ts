import { useEffect, useState } from 'react';
import { tutorApi, type TutorSummary } from './tutorApi';

/**
 * Polls the class totals for the wall screen. A failed poll keeps the last totals: the
 * screen is a decoration, not an alarm.
 *
 * @param {number} [pollingIntervalMs=4000] - Refresh period.
 * @returns {TutorSummary | null} Null until the first answer.
 */
export function useTutorSummary(pollingIntervalMs = 4000): TutorSummary | null {
  const [summary, setSummary] = useState<TutorSummary | null>(null);

  useEffect(() => {
    let active = true;
    const refresh = () =>
      tutorApi
        .summary()
        .then((next) => {
          if (active) setSummary(next);
        })
        .catch(() => undefined);
    void refresh();
    const timer = setInterval(refresh, pollingIntervalMs);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [pollingIntervalMs]);

  return summary;
}
