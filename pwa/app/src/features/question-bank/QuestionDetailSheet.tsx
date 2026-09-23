import React from 'react';
import { Check } from 'lucide-react';
import { Sheet } from '../../shared/ui/Sheet/Sheet';
import { OPTION_LETTERS } from '../../shared/constants/options';
import {
  getMisconceptionLabel,
  getSubconceptLabel,
  getTopicLabel,
} from '../../shared/taxonomy/labels';
import styles from './QuestionDetailSheet.module.css';
import { BankQuestion } from './bankApi';

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
      <div className={styles.detail}>
        <b className={styles.title}>{question.question_text}</b>
        {OPTION_LETTERS.map((k) => {
          const distractor = question.distractors[k];
          const miscLabel = distractor
            ? getMisconceptionLabel(distractor.misconception)
            : '';
          return (
            <div key={k} className={styles.option}>
              <b>{k}:</b> {question.options[k]}
              {k === question.correct_option ? (
                <Check size={14} aria-hidden className={styles.check} />
              ) : null}
              {k !== question.correct_option && distractor && (
                <span className={styles.distractor}>
                  {' '}
                  — {miscLabel ? `${miscLabel}: ` : ''}
                  {distractor.explanation}
                </span>
              )}
            </div>
          );
        })}
        <div className={styles.meta}>
          {topicLabel}
          {subconceptLabel ? ` · ${subconceptLabel}` : ''}
          {question.source ? ` · ${question.source}` : ''}{' '}
          {question.sympy_verified ? '· verificada' : ''}
        </div>
      </div>
    </Sheet>
  );
};
