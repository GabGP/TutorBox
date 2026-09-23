import { requestApi } from '../../shared/api/httpClient';
import { toQuery } from '../../shared/api/query';
import {
  FullGenerationMetrics,
  GenerateQuestionResponse,
  GenerationLogItem,
  GenerationMetrics,
  TopicModel,
} from './generator.types';

/**
 * API client contract for dynamic quiz question generation and taxonomy discovery.
 */
export const generatorApi = {
  /**
   * Discovers available mathematical topics and subconcepts from `/quiz/topics`.
   *
   * @returns {Promise<TopicModel[]>} List of available topic schemas and descriptions.
   */
  async getTopics(): Promise<TopicModel[]> {
    return requestApi<TopicModel[]>('GET', '/quiz/topics', undefined, false);
  },

  /**
   * Retrieves telemetry metrics including average generation duration for a topic.
   *
   * @param {string} [topic] - Optional topic filter.
   * @returns {Promise<GenerationMetrics>} Generation duration and count telemetry.
   */
  async getMetrics(topic?: string): Promise<GenerationMetrics> {
    return requestApi<GenerationMetrics>(
      'GET',
      `/quiz/generation-metrics${toQuery({ topic })}`,
      undefined,
      true
    );
  },

  /**
   * Retrieves full telemetry metrics (reliability + latency) with filters.
   */
  async getFullMetrics(params?: {
    topic?: string;
    model_name?: string;
  }): Promise<FullGenerationMetrics> {
    return requestApi<FullGenerationMetrics>(
      'GET',
      `/quiz/generation-metrics${toQuery({ topic: params?.topic, model_name: params?.model_name })}`
    );
  },

  /**
   * Lists generation attempt logs via `GET /quiz/generation-logs`.
   */
  async getLogs(params?: {
    topic?: string;
    user_id?: number;
    success?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<{ logs: GenerationLogItem[]; total: number }> {
    return requestApi(
      'GET',
      `/quiz/generation-logs${toQuery({
        topic: params?.topic,
        user_id: params?.user_id,
        success: params?.success,
        limit: params?.limit ?? 20,
        offset: params?.offset ?? 0,
      })}`
    );
  },

  /**
   * Initiates dynamic LLM quiz question generation with SymPy math validation via `POST /quiz/generate`.
   *
   * @param {object} payload - Generation parameters.
   * @param {string} payload.topic - Math topic slug.
   * @param {string | null} [payload.subconcept] - Optional curriculum subconcept.
   * @param {boolean} payload.save_to_bank - Whether to persist generated question to the SQLite question bank.
   * @returns {Promise<GenerateQuestionResponse>} Newly generated, validated multiple-choice question.
   */
  async generateQuestion(payload: {
    topic: string;
    subconcept?: string | null;
    save_to_bank: boolean;
  }): Promise<GenerateQuestionResponse> {
    return requestApi<GenerateQuestionResponse>('POST', '/quiz/generate', payload);
  },
};
