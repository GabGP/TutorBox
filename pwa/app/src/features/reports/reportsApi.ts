import { requestApi } from '../../shared/api/httpClient';

export type ReportPeriod = 'day' | 'week' | 'month';

export interface QuizTopicScore {
  topic: string;
  answers: number;
  correct: number;
  accuracy: number;
  previous_accuracy: number | null;
  change: number | null;
}

export interface QuizReport {
  start: string;
  end: string;
  students: number;
  answers: number;
  accuracy: number;
  best_topic: string | null;
  weakest_topic: string | null;
  most_improved_topic: string | null;
  topics: QuizTopicScore[];
  misconceptions: { misconception: string; topic: string; wrong_answers: number }[];
}

export interface TutorTopicActivity {
  topic: string;
  turns: number;
  students: number;
  solved: number;
  stuck: number;
}

export interface TutorSessionSummary {
  student: string;
  started_at: string;
  last_turn_at: string;
  turns: number;
  topics: string[];
  solved: number;
  stuck: number;
}

export interface TutorReport {
  start: string;
  end: string;
  students: number;
  sessions: number;
  turns: number;
  most_asked_topic: string | null;
  most_stuck_topic: string | null;
  topics: TutorTopicActivity[];
  session_summaries: TutorSessionSummary[];
}

/** Teacher-only analytics (`GET /quiz/analytics`, `GET /tutor/analytics`). */
export const reportsApi = {
  quiz: (period: ReportPeriod) =>
    requestApi<QuizReport>('GET', `/quiz/analytics?period=${period}`),
  tutor: (period: ReportPeriod) =>
    requestApi<TutorReport>('GET', `/tutor/analytics?period=${period}`),
};
