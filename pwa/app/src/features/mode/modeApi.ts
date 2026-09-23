import { requestApi } from '../../shared/api/httpClient';

/** Classroom-wide mode the teacher picks from /maestro/ (docs/api/system.md#classroom-mode). */
export type ApplianceMode = 'quiz' | 'tutor' | 'apps';

/**
 * API client for the classroom mode switch.
 */
export const modeApi = {
  /** Public: the class screen and student phones read it before anyone logs in. */
  async getMode(): Promise<ApplianceMode> {
    const { mode } = await requestApi<{ mode: ApplianceMode }>('GET', '/mode', undefined, false);
    return mode;
  },

  /** Teacher/admin only; the backend answers 409 while a quiz round is live. */
  async setMode(mode: ApplianceMode): Promise<ApplianceMode> {
    const res = await requestApi<{ mode: ApplianceMode }>('PUT', '/mode', { mode });
    return res.mode;
  },
};
