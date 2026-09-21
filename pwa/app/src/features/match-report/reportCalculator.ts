import { OPTION_LETTERS } from '../../shared/constants/options';
import { QuestionErrorSummary, StoredRoundHistory, TopWrongAnswer } from './report.types';

/**
 * Identifies the single most common incorrect distractor chosen in a quiz round,
 * filtering for significance (minimum 2 votes).
 *
 * @param {StoredRoundHistory} item - The stored round record with question details and tally counts.
 * @returns {TopWrongAnswer | null} The top wrong choice and vote count, or null if insignificant.
 */
export function findTopWrong(item: StoredRoundHistory): TopWrongAnswer | null {
  const wrongEntries = OPTION_LETTERS
    .filter((k) => k !== item.tally.correct_option)
    .map((k) => [k, item.tally.counts[k] || 0] as const)
    .sort((a, b) => b[1] - a[1]);

  const top = wrongEntries[0];
  return top && top[1] >= 2 ? { choice: top[0], count: top[1] } : null;
}

/**
 * Returns the lowest-scoring questions in a match, sorted ascending by correct answer percentage.
 *
 * @param {StoredRoundHistory[]} history - Complete list of finished rounds in the match.
 * @param {number} [limit=3] - Maximum number of hardest questions to return.
 * @returns {StoredRoundHistory[]} Subset of questions with the lowest accuracy.
 */
export function getHardestQuestions(
  history: StoredRoundHistory[],
  limit = 3
): StoredRoundHistory[] {
  return [...history]
    .sort((a, b) => a.tally.correct_percentage - b.tally.correct_percentage)
    .slice(0, limit);
}

/**
 * Extracts questions that experienced repeated conceptual misunderstandings (clustered wrong answers).
 *
 * @param {StoredRoundHistory[]} history - Complete match round history.
 * @param {number} [limit=3] - Maximum number of error summaries to extract.
 * @returns {QuestionErrorSummary[]} Summaries of rounds with high distractor concentration.
 */
export function getTopRepeatedErrors(
  history: StoredRoundHistory[],
  limit = 3
): QuestionErrorSummary[] {
  return history
    .map((h) => ({ history: h, wrong: findTopWrong(h) }))
    .filter((x): x is QuestionErrorSummary => x.wrong !== null)
    .sort((a, b) => b.wrong.count - a.wrong.count)
    .slice(0, limit);
}

/**
 * Determines the visual tone token (CSS color variable) based on the percentage score.
 *
 * @param {number} percentage - Score percentage (0 to 100).
 * @returns {string} CSS variable representing warning, medium, or positive tone.
 */
export function getToneColor(percentage: number): string {
  if (percentage < 40) return 'var(--bad)';
  if (percentage < 70) return 'var(--warn)';
  return 'var(--ok)';
}
