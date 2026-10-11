import { requestApi } from '../../shared/api/httpClient';
import type { ClassPresence } from './presence.types';

/**
 * API client for classroom presence: a student's phone sends heartbeats,
 * and the teacher's lobby reads the class list.
 */
export const presenceApi = {
  /** Tells the server this student's phone is still waiting in the class. Answers 204 with no body. */
  async sendHeartbeat(): Promise<void> {
    await requestApi('POST', '/presence/heartbeat');
  },

  /** Every student with the state of their phone and clicker (teachers only). */
  getClassPresence: (): Promise<ClassPresence> =>
    requestApi<ClassPresence>('GET', '/presence/class'),
};
