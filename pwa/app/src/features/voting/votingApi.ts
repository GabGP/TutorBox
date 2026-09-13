import { requestApi } from '../../shared/api/httpClient';
import { VotePayload, VoteResponse } from './voting.types';

/**
 * API client contract for student and clicker vote ingestion.
 */
export const votingApi = {
  /**
   * Submits a student vote for the active round via `POST /session/{id}/vote`.
   * Enforces first-press lock semantics on the backend.
   *
   * @param {string} sessionId - Active session UUID.
   * @param {VotePayload} payload - Vote submission payload with selected option and latency metadata.
   * @returns {Promise<VoteResponse>} Confirmation response containing the recorded vote.
   */
  async submitVote(sessionId: string, payload: VotePayload): Promise<VoteResponse> {
    return requestApi<VoteResponse>('POST', `/session/${sessionId}/vote`, payload);
  },
};
