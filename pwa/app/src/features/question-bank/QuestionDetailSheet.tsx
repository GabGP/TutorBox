import React from 'react';
import { Sheet } from '../../shared/ui/Sheet/Sheet';
import {
  getMisconceptionLabel,
  getSubconceptLabel,
  getTopicLabel,
} from '../question-generator/TopicSelector';
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
  const topicLabel = getTopicLabel(question.topic);
  const subconceptLabel = getSubconceptLabel(question.subconcept) || question.subconcept;
  return (
    <Sheet label={`Detalle pregunta ${question.id}`} onClose={onClose}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <b style={{ fontSize: '16px' }}>{question.question_text}</b>
        {OPTION_KEYS.map((k) => {
          const distractor = question.distractors[k];
          const miscLabel = distractor
            ? getMisconceptionLabel(distractor.misconception)
            : '';
          return (
            <div key={k} style={{ fontSize: '14px' }}>
              <b>{k}:</b> {question.options[k]}
              {k === question.correct_option ? ' ✔' : ''}
              {k !== question.correct_option && distractor && (
                <span style={{ color: 'var(--mute2)' }}>
                  {' '}
                  — {miscLabel ? `${miscLabel}: ` : ''}
                  {distractor.explanation}
                </span>
              )}
            </div>
          );
        })}
        <div style={{ color: 'var(--mute2)', fontSize: '13px', marginTop: '4px' }}>
          {topicLabel}
          {subconceptLabel ? ` · ${subconceptLabel}` : ''}
          {question.source ? ` · ${question.source}` : ''}{' '}
          {question.sympy_verified ? '· verificada' : ''}
        </div>
      </div>
    </Sheet>
  );
};
