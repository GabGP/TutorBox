export interface StoredStudentVotes {
  votes: Record<string, 'A' | 'B' | 'C' | 'D'>;
  hits: Record<string, boolean>;
}

export interface StoredRoundHistory {
  round_id: string;
  text: string;
  options: Record<string, string>;
  tally: {
    counts: Record<string, number>;
    total_votes: number;
    correct_option: string;
    correct_count: number;
    correct_percentage: number;
  };
  explanations: Record<string, string>;
}

export interface StoredVoicePreference {
  engine?: string;
  voice?: string;
  lang?: string;
}

/**
 * Centralized browser localStorage adapter for session tokens, session IDs, and vote histories.
 */
export const storage = {
  /** Retrieves the stored authentication Bearer token. */
  getToken: (): string | null => localStorage.getItem('tb_token'),

  /** Persists the authentication Bearer token. */
  setToken: (token: string): void => localStorage.setItem('tb_token', token),

  /** Removes the authentication Bearer token from localStorage. */
  clearToken: (): void => localStorage.removeItem('tb_token'),

  /** Retrieves the active teacher session UUID. */
  getTeacherSessionId: (): string | null => localStorage.getItem('tb_session'),

  /** Persists the active teacher session UUID. */
  setTeacherSessionId: (id: string): void => localStorage.setItem('tb_session', id),

  /** Clears the active teacher session UUID. */
  clearTeacherSessionId: (): void => localStorage.removeItem('tb_session'),

  /** Retrieves the last known student session UUID. */
  getLastStudentSessionId: (): string | null => localStorage.getItem('tb_last_session'),

  /** Persists the last known student session UUID. */
  setLastStudentSessionId: (id: string): void => localStorage.setItem('tb_last_session', id),

  /**
   * Retrieves recorded votes and hits for a specific quiz session.
   *
   * @param {string} sessionId - Target session ID.
   * @returns {StoredStudentVotes} Stored student vote records and hits.
   */
  getStudentVotes: (sessionId: string): StoredStudentVotes => {
    try {
      const raw = localStorage.getItem(`tb_votes_${sessionId}`);
      return raw ? JSON.parse(raw) : { votes: {}, hits: {} };
    } catch {
      return { votes: {}, hits: {} };
    }
  },

  /**
   * Persists student votes and correctness records for a quiz session.
   *
   * @param {string} sessionId - Target session ID.
   * @param {StoredStudentVotes} data - Vote and hit records to persist.
   * @returns {void}
   */
  setStudentVotes: (sessionId: string, data: StoredStudentVotes): void => {
    localStorage.setItem(`tb_votes_${sessionId}`, JSON.stringify(data));
  },

  /**
   * Retrieves the historical rounds record for a teacher match report.
   *
   * @param {string} sessionId - Target session ID.
   * @returns {StoredRoundHistory[]} Stored array of finished round records.
   */
  getRoundHistory: (sessionId: string): StoredRoundHistory[] => {
    try {
      const raw = localStorage.getItem(`tb_hist_${sessionId}`);
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  },

  /**
   * Persists historical rounds for a teacher match report.
   *
   * @param {string} sessionId - Target session ID.
   * @param {StoredRoundHistory[]} history - List of round records to store.
   * @returns {void}
   */
  setRoundHistory: (sessionId: string, history: StoredRoundHistory[]): void => {
    localStorage.setItem(`tb_hist_${sessionId}`, JSON.stringify(history));
  },

  /** Retrieves the teacher's preferred TTS voice selection. */
  getVoicePreference: (): StoredVoicePreference | null => {
    try {
      const raw = localStorage.getItem('tb_voice');
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },

  /** Persists the teacher's preferred TTS voice selection. */
  setVoicePreference: (pref: StoredVoicePreference): void => {
    localStorage.setItem('tb_voice', JSON.stringify(pref));
  },
};
