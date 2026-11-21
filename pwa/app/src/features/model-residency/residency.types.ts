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
  /** After a load: the share of the model on the GPU (0-100). Below 100 it runs slowly. */
  gpu_percent?: number | null;
}

/** Whether the request asked for the model to be loaded or unloaded. */
export type ResidencyDirection = 'load' | 'unload';
