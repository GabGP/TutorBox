import { StoredRoundHistory } from '../../shared/lib/storage';

export type { StoredRoundHistory };

export interface TopWrongAnswer {
  choice: string;
  count: number;
}

export interface QuestionErrorSummary {
  history: StoredRoundHistory;
  wrong: TopWrongAnswer;
}
