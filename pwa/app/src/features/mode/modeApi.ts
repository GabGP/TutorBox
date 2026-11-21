import { requestApi } from '../../shared/api/httpClient';
import type { ModelResidency } from '../model-residency/residency.types';

/** Classroom-wide mode the teacher picks from /maestro/ (docs/api/system.md#classroom-mode). */
export type ApplianceMode = 'quiz' | 'tutor' | 'apps';

/** What the backend saved (`mode`) and what it did with the tutor model (`model`). */
export interface ModeChange {
  mode: ApplianceMode;
  model: ModelResidency;
}

/**
 * API client for the classroom mode switch.
 */
export const modeApi = {
  /** Public: the class screen and student phones read it before anyone logs in. */
  async getMode(): Promise<ApplianceMode> {
    const { mode } = await requestApi<{ mode: ApplianceMode }>('GET', '/mode', undefined, false);
    return mode;
  },

  /**
   * Teacher/admin only; the backend answers 409 while a quiz round is live. The answer also
   * says what happened to the tutor model (loaded for tutor mode, unloaded when leaving it).
   */
  async setMode(mode: ApplianceMode): Promise<ModeChange> {
    return requestApi<ModeChange>('PUT', '/mode', { mode });
  },
};
