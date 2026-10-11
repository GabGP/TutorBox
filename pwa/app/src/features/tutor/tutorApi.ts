import { requestApi } from '../../shared/api/httpClient';

/** The tutor's plain-text Spanish reply to one message. */
export interface TutorReply {
  reply: string;
  kind: string;
  hint_level: number;
  used_model: boolean;
  topic: string | null;
}

/** One student on the teacher's tutor panel. */
export interface TutorStudent {
  username: string;
  online: boolean;
  seconds_ago: number;
  turns: number;
  solved: number;
  problem: string | null;
  hint_level: number;
}

/** Class totals for the wall screen: counts only, no names. */
export interface TutorSummary {
  online: number;
  solved: number;
  need_help: number;
}

/**
 * Mode 2 API client: students chat with the Socratic tutor, teachers watch who is using it.
 */
export const tutorApi = {
  /** Sends one message (plain text only) and returns the tutor's reply. */
  send: (message: string) => requestApi<TutorReply>('POST', '/tutor/message', { message }),

  /** Forgets the problem in progress ("Empezar de nuevo"). */
  reset: () => requestApi<{ status: string }>('POST', '/tutor/reset', {}),

  /** Tells the teacher's panel that this student's chat is open. */
  ping: () => requestApi<{ status: string }>('POST', '/tutor/ping', {}),

  /** Totals for the classroom screen, which has no login. */
  summary: () => requestApi<TutorSummary>('GET', '/tutor/summary', undefined, false),

  /** Students using the tutor, connected ones first (teachers only). */
  students: async (): Promise<TutorStudent[]> =>
    (await requestApi<{ students: TutorStudent[] }>('GET', '/tutor/students')).students,
};
