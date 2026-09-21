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
}

export const PROGRESS_ANIMATION = {
  STAGE_SPEED_SECONDS: 5,
  SHIMMER_SPEED_SECONDS: 5,
  CYCLE_SPEED_SECONDS: 5,
  ORBIT_SPEED_SECONDS: 3.6,
  DEFAULT_QUESTION_ETA_SECONDS: 12,
  MOBILE_PILL_COLS_MAX: 5,
  DESKTOP_PILL_COLS_MAX: 10,
} as const;

export const PEDAGOGICAL_STAGES = [
  'Redactando el enunciado del problema...',
  'Diseñando opciones para dudas frecuentes...',
  'Comprobando la exactitud de los cálculos...',
  'Guardando en el banco del dispositivo...',
] as const;
