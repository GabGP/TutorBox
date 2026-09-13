export interface SubconceptModel {
  name: string;
  description?: string;
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

export interface GenerationProgress {
  done: number;
  total: number;
  failed: number;
  ids: string[];
  eta: number | null;
}
