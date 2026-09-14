import { requestApi } from '../../shared/api/httpClient';
import {
  GenerateQuestionResponse,
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
    const query = topic ? `?topic=${encodeURIComponent(topic)}` : '';
    return requestApi<GenerationMetrics>(
      'GET',
      `/quiz/generation-metrics${query}`,
      undefined,
      true
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
