import { requestApi } from '../../shared/api/httpClient';
import { toQuery } from '../../shared/api/query';

export interface DistractorDetail {
  misconception: string;
  explanation: string;
}

/**
 * Question shape lineage (deliberately separate DTOs, same core):
 * - `BankQuestion` (here): persisted bank rows with distractors + sympy flags.
 * - `GeneratedQuestion` (generator.types): fresh LLM output before persistence.
 * - `QuestionModel` (session.types): slim round payload (text + options only).
 * All three share the `id/text/options/topic` core; each layer extends only
 * what it needs so wire payloads stay small.
 */
export interface BankQuestion {
  id: string;
  topic: string;
  subconcept: string;
  question_text: string;
  options: Record<string, string>;
  correct_option: string;
  distractors: Record<string, DistractorDetail>;
  source?: string;
  sympy_verified?: boolean;
  created_at?: string | null;
}

export interface BankQuestionCreate extends Omit<BankQuestion, 'id'> {
  id?: string | null;
}

export interface ValidationResult {
  is_valid: boolean;
  errors: string[];
  details: Record<string, string>;
}

/**
 * API client contract for manual question-bank management.
 * Covers the quiz endpoints the generator flow never touches:
 * list/detail, manual create, soft-delete, standalone math validation,
 * and the canonical JSON schema contract.
 */
export const bankApi = {
  async listQuestions(params?: {
    topic?: string;
    subconcept?: string;
    limit?: number;
    offset?: number;
  }): Promise<{ questions: BankQuestion[]; total: number }> {
    return requestApi(
      'GET',
      `/quiz/questions${toQuery({
        topic: params?.topic,
        subconcept: params?.subconcept,
        limit: params?.limit ?? 5,
        offset: params?.offset ?? 0,
      })}`
    );
  },

  async getQuestion(id: string): Promise<BankQuestion> {
    return requestApi('GET', `/quiz/questions/${encodeURIComponent(id)}`);
  },

  async createQuestion(payload: BankQuestionCreate): Promise<BankQuestion> {
    return requestApi<BankQuestion>('POST', '/quiz/questions', payload);
  },

  async updateQuestion(
    id: string,
    payload: BankQuestionCreate
  ): Promise<BankQuestion> {
    return requestApi<BankQuestion>(
      'PUT',
      `/quiz/questions/${encodeURIComponent(id)}`,
      payload
    );
  },

  async deleteQuestion(id: string): Promise<void> {
    await requestApi('DELETE', `/quiz/questions/${encodeURIComponent(id)}`);
  },

  async validateQuestion(question: BankQuestion): Promise<ValidationResult> {
    return requestApi<ValidationResult>('POST', '/quiz/validate', {
      question,
    });
  },

  async getSchema(): Promise<Record<string, unknown>> {
    return requestApi('GET', '/quiz/schema');
  },
};
