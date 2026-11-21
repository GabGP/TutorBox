/** What the backend did with one model (backend/src/core/llm/residency, see docs/api/system.md). */
export type ModelResidencyAction = 'loaded' | 'unloaded' | 'kept' | 'unsupported' | 'failed' | 'disabled';

export interface ModelResidency {
  /** Ollama model name, e.g. qwen2.5:3b. */
  model: string;
  action: ModelResidencyAction;
  /** Load time in milliseconds; null for an unload. */
  duration_ms: number | null;
  /** Server-side reason; for logs only, never shown to the teacher. */
  detail: string | null;
}

/** Whether the request asked for the model to be loaded or unloaded. */
export type ResidencyDirection = 'load' | 'unload';
