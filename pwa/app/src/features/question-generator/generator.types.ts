export interface SubconceptModel {
  name: string;
  description?: string;
  /** Diagnosed misconception slugs for this subconcept (from /quiz/topics). */
  misconceptions?: string[];
}

export interface TopicModel {
  name: string;
  label?: string;
  glyph?: string;
  subconcepts: SubconceptModel[];
}

export interface GenerationMetrics {
  topic: string;
  total_generated: number;
  avg_duration_ms: number;
}

export interface FullGenerationMetrics {
  total_generations: number;
  successful_generations: number;
  failed_generations: number;
  success_rate: number;
  avg_attempts: number;
  avg_duration_ms: number;
}

export interface GenerationLogItem {
  id: number;
  question_id?: string | null;
  user_id: number;
  topic: string;
  subconcept?: string | null;
  model_name: string;
  attempts: number;
  duration_ms: number;
  success: boolean;
  rejection_history: string[];
  created_at?: string | null;
}

export interface GeneratedQuestion {
  id: string;
  question_text: string;
  options: Record<string, string>;
  topic?: string;
  subconcept?: string;
}

export interface GenerateQuestionResponse {
  question: GeneratedQuestion;
}

export type QuestionGenerationStatus = 'pending' | 'generating' | 'success' | 'failed';

export interface GenerationProgress {
  done: number;
  total: number;
  failed: number;
  ids: string[];
  eta: number | null;
  currentTopic?: string;
  currentSubconcept?: string | null;
  currentIndex?: number;
  statuses?: QuestionGenerationStatus[];
  /** True while the quiz model loads before the first question (the card shows a loading line). */
  modelLoading?: boolean;
  /**
   * Wall-clock times (Date.now() ms) owned by the batch, not by the progress card: the card
   * unmounts when the teacher switches tab, and its timers must go on from these on return.
   */
  startedAtMs?: number;
  /** When the current question was sent to the model. */
  questionStartedAtMs?: number;
  /** When the batch ended; the elapsed time stays at this value afterwards. */
  finishedAtMs?: number;
}

export { PEDAGOGICAL_STAGES, PROGRESS_ANIMATION } from './generator.constants';
