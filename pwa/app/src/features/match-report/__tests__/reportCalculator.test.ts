import { describe, expect, it } from 'vitest';
import {
  findTopWrong,
  getHardestQuestions,
  getToneColor,
  getTopRepeatedErrors,
} from '../reportCalculator';
import { StoredRoundHistory } from '../report.types';

describe('Match Report Calculator', () => {
  const mockHistoryItem = (
    id: string,
    text: string,
    percentage: number,
    counts: Record<string, number>,
    correct = 'A'
  ): StoredRoundHistory => ({
    round_id: id,
    text,
    options: { A: '4', B: '5', C: '6', D: '7' },
    tally: {
      counts,
      total_votes: Object.values(counts).reduce((a, b) => a + b, 0),
      correct_option: correct,
      correct_count: counts[correct] || 0,
      correct_percentage: percentage,
    },
    explanations: {
      B: 'Error común sumando en vez de multiplicar',
      C: 'Error de orden de operaciones',
    },
  });

  describe('findTopWrong', () => {
    it('returns highest wrong choice when count >= 2', () => {
      const item = mockHistoryItem('r1', 'Q1', 50, { A: 5, B: 4, C: 1, D: 0 });
      expect(findTopWrong(item)).toEqual({ choice: 'B', count: 4 });
    });

    it('returns null when all wrong choices have fewer than 2 votes', () => {
      const item = mockHistoryItem('r2', 'Q2', 80, { A: 8, B: 1, C: 1, D: 0 });
      expect(findTopWrong(item)).toBeNull();
    });
  });

  describe('getHardestQuestions', () => {
    it('orders ascending by accuracy percentage and limits to top 3', () => {
      const h1 = mockHistoryItem('r1', 'Easy', 90, { A: 9 });
      const h2 = mockHistoryItem('r2', 'Hardest', 20, { A: 2 });
      const h3 = mockHistoryItem('r3', 'Medium', 60, { A: 6 });
      const h4 = mockHistoryItem('r4', 'Harder', 35, { A: 3 });

      const hardest = getHardestQuestions([h1, h2, h3, h4], 3);
      expect(hardest.map((h) => h.round_id)).toEqual(['r2', 'r4', 'r3']);
    });
  });

  describe('getTopRepeatedErrors', () => {
    it('ranks repeated distractor errors by count descending', () => {
      const h1 = mockHistoryItem('r1', 'Q1', 40, { A: 4, B: 6, C: 0, D: 0 }); // B: 6
      const h2 = mockHistoryItem('r2', 'Q2', 50, { A: 5, B: 2, C: 3, D: 0 }); // C: 3
      const h3 = mockHistoryItem('r3', 'Q3', 90, { A: 9, B: 1, C: 0, D: 0 }); // none >= 2

      const topErrors = getTopRepeatedErrors([h1, h2, h3]);
      expect(topErrors).toHaveLength(2);
      expect(topErrors[0].wrong).toEqual({ choice: 'B', count: 6 });
      expect(topErrors[1].wrong).toEqual({ choice: 'C', count: 3 });
    });
  });

  describe('getToneColor', () => {
    it('maps color tokens according to thresholds', () => {
      expect(getToneColor(39)).toBe('var(--bad)');
      expect(getToneColor(40)).toBe('var(--C)');
      expect(getToneColor(69)).toBe('var(--C)');
      expect(getToneColor(70)).toBe('var(--D)');
      expect(getToneColor(100)).toBe('var(--D)');
    });
  });
});
