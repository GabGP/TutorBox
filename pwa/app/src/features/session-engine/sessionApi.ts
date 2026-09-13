import { requestApi } from '../../shared/api/httpClient';
import { SessionModel, SessionReport } from './session.types';

/**
 * Extracts an optional pinned session UUID from the window query parameters (`?s=<uuid>`).
 *
 * @returns {string | null} The session ID query parameter value, or null if unpinned or in SSR.
 */
export function getSessionQueryParamId(): string | null {
  if (typeof window === 'undefined') return null;
  return new URLSearchParams(window.location.search).get('s');
}

/**
 * Builds the canonical API endpoint path for the active or pinned session.
 *
 * @returns {string} The relative session route (e.g. `/session/<uuid>` or `/session/current`).
 */
export function getSessionPath(): string {
  const pinnedId = getSessionQueryParamId();
  return `/session/${pinnedId || 'current'}`;
}

/**
 * API client contract for managing quiz sessions, round transitions, and match reports.
 */
export const sessionApi = {
  /**
   * Retrieves active or query-pinned quiz session state without authentication.
   *
   * @returns {Promise<SessionModel>} Current session model snapshot.
   */
  async getCurrentSession(): Promise<SessionModel> {
    return requestApi<SessionModel>('GET', getSessionPath(), undefined, false);
  },

  /**
   * Retrieves specific session state by explicit UUID.
   *
   * @param {string} id - Session UUID.
   * @returns {Promise<SessionModel>} Target session model snapshot.
   */
  async getSessionById(id: string): Promise<SessionModel> {
    return requestApi<SessionModel>('GET', `/session/${id}`, undefined, false);
  },

  /**
   * Creates a new quiz match in lobby state via `POST /session`.
   *
   * @param {object} payload - Session configuration.
   * @param {string} payload.title - Match title.
   * @param {string} payload.topic - Math topic slug.
   * @param {string[]} payload.question_ids - Ordered list of question IDs.
   * @param {number} payload.duration_seconds - Countdown duration per round.
   * @returns {Promise<SessionModel>} Created session snapshot.
   */
  async createSession(payload: {
    title: string;
    topic: string;
    question_ids: string[];
    duration_seconds: number;
  }): Promise<SessionModel> {
    return requestApi<SessionModel>('POST', '/session', payload);
  },

  /**
   * Opens the first question round and starts countdown via `POST /session/{id}/start`.
   *
   * @param {string} id - Session UUID.
   * @returns {Promise<SessionModel>} Active session snapshot with round 1 opened.
   */
  async startSession(id: string): Promise<SessionModel> {
    return requestApi<SessionModel>('POST', `/session/${id}/start`);
  },

  /**
   * Closes the active round's voting window via `POST /session/{id}/close`.
   *
   * @param {string} id - Session UUID.
   * @returns {Promise<void>}
   */
  async closeRound(id: string): Promise<void> {
    await requestApi('POST', `/session/${id}/close`);
  },

  /**
   * Computes vote tallies, evaluates >51% Rule, and reveals answers via `POST /session/{id}/reveal`.
   *
   * @param {string} id - Session UUID.
   * @returns {Promise<void>}
   */
  async revealRound(id: string): Promise<void> {
    await requestApi('POST', `/session/${id}/reveal`);
  },

  /**
   * Advances the match to the next question or completes the match via `POST /session/{id}/next`.
   *
   * @param {string} id - Session UUID.
   * @returns {Promise<SessionModel>} Updated session snapshot.
   */
  async nextRound(id: string): Promise<SessionModel> {
    return requestApi<SessionModel>('POST', `/session/${id}/next`);
  },

  /**
   * Retrieves summary statistics and accuracy report for a finished match via `GET /session/{id}/report`.
   *
   * @param {string} id - Session UUID.
   * @returns {Promise<SessionReport>} Aggregate performance metrics.
   */
  async getSessionReport(id: string): Promise<SessionReport> {
    return requestApi<SessionReport>('GET', `/session/${id}/report`);
  },
};
