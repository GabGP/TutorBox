export type SessionStatus = 'lobby' | 'active' | 'completed' | 'abandoned';
export type RoundStatus = 'pending' | 'open' | 'closed' | 'revealed';

export interface QuestionModel {
  id: string;
  question_text: string;
  options: Record<string, string>;
  topic?: string;
  subconcept?: string;
}

export interface RoundTally {
  counts: Record<string, number>;
  total_votes: number;
  correct_option: string;
  correct_count: number;
  correct_percentage: number;
}

export interface RoundDecision {
  should_speak: boolean;
  dominant_distractor: string;
  dominant_percentage: number;
  explanation: string;
}

export interface RoundResult {
  tally: RoundTally;
  decision: RoundDecision;
  explanations: Record<string, string>;
}

export interface RoundModel {
  round_id: string;
  round_index: number;
  duration_seconds: number;
  time_remaining: number | null;
  status: RoundStatus;
  votes_cast: number;
  question?: QuestionModel;
  result?: RoundResult;
}

export interface SessionModel {
  id: string;
  title: string;
  topic: string;
  status: SessionStatus;
  question_count: number;
  current_round_index: number;
  current_round?: RoundModel;
  created_at: string;
  closed_at?: string;
}

export interface SessionReport {
  session_id: string;
  total_rounds: number;
  total_votes_cast: number;
  average_accuracy_percentage: number;
}
