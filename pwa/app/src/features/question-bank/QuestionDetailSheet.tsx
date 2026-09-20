import React from 'react';
import { Sheet } from '../../shared/ui/Sheet/Sheet';
import { BankQuestion } from './bankApi';

const OPTION_KEYS = ['A', 'B', 'C', 'D'] as const;

export interface QuestionDetailSheetProps {
  /** Null = closed. */
  question: BankQuestion | null;
  onClose: () => void;
}

/**
 * Read-only detail card for a bank question: options with the correct
 * mark, distractor explanations, and bank metadata.
 */
export const QuestionDetailSheet: React.FC<QuestionDetailSheetProps> = ({
  question,
  onClose,
}) => {
  if (!question) return null;
  return (
    <Sheet label={`Detalle pregunta ${question.id}`} onClose={onClose}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <b style={{ fontSize: '16px' }}>{question.question_text}</b>
        {OPTION_KEYS.map((k) => (
          <div key={k} style={{ fontSize: '14px' }}>
            <b>{k}:</b> {question.options[k]}
            {k === question.correct_option ? ' ✔' : ''}
            {k !== question.correct_option && question.distractors[k] && (
              <span style={{ color: 'var(--mute2)' }}>
                {' '}
                — {question.distractors[k].explanation}
              </span>
            )}
          </div>
        ))}
        <div style={{ color: 'var(--mute2)', fontSize: '13px', marginTop: '4px' }}>
          {question.subconcept} · {question.source || ''}{' '}
          {question.sympy_verified ? '· verificada' : ''}
        </div>
      </div>
    </Sheet>
  );
};
