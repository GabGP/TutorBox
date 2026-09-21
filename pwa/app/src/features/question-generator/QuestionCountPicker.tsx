import React from 'react';
import { Minus, Plus } from 'lucide-react';
import { QUESTION_COUNT_MAX, QUESTION_COUNT_MIN } from './generator.constants';
import styles from './generator.module.css';

export interface QuestionCountPickerProps {
  count: number;
  topicLabel: string;
  onChangeCount: (newCount: number) => void;
  errorNote?: string | null;
}

/**
 * Question Count Picker component.
 * Allows teachers to increment/decrement the targeted question count
 * (shared QUESTION_COUNT_MIN–MAX range) with estimated duration
 * calculations and selected topic confirmation.
 *
 * @param {QuestionCountPickerProps} props - Component props controlling count, topic label, and callbacks.
 * @returns {JSX.Element} The rendered counter control panel.
 */
export const QuestionCountPicker: React.FC<QuestionCountPickerProps> = ({
  count,
  topicLabel,
  onChangeCount,
  errorNote,
}) => {
  const estimatedMinutes = Math.max(2, Math.round(count * 0.6));

  const handleDecrement = () => {
    onChangeCount(Math.max(QUESTION_COUNT_MIN, count - 1));
  };

  const handleIncrement = () => {
    onChangeCount(Math.min(QUESTION_COUNT_MAX, count + 1));
  };

  return (
    <div className={styles.stack}>
      <div className={styles.counter}>
        <div className={styles.num} id="count">
          {count}
        </div>
        <div className={styles.sub}>
          preguntas · aprox. <span id="minutes">{estimatedMinutes}</span> min de juego
        </div>
        <div className={styles.pm}>
          <button
            type="button"
            id="dec"
            aria-label="Una pregunta menos"
            onClick={handleDecrement}
          >
            <Minus size={28} aria-hidden />
          </button>
          <button
            type="button"
            id="inc"
            className={styles.p}
            aria-label="Una pregunta más"
            onClick={handleIncrement}
          >
            <Plus size={28} aria-hidden />
          </button>
        </div>
      </div>

      <div className={styles.infoCard}>
        <div className={styles.h}>Tema elegido</div>
        <div className={styles.pText} id="topicLabel">
          {topicLabel}
        </div>
      </div>

      <p className={styles.description}>
        El modelo local escribe cada pregunta y la revisa con matemáticas antes de usarla. Cada pregunta dura 20 segundos.
      </p>

      {errorNote && (
        <div className={styles.note} id="countNote">
          {errorNote}
        </div>
      )}
    </div>
  );
};
