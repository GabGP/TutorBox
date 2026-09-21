import React from 'react';
import { Minus, Plus } from 'lucide-react';
import styles from './generator.module.css';

export interface QuestionCountPickerProps {
  count: number;
  topicLabel: string;
  onChangeCount: (newCount: number) => void;
  errorNote?: string | null;
}

/**
 * Question Count Picker component.
 * Allows teachers to increment/decrement the targeted question count (range 3–20)
 * with estimated duration calculations and selected topic confirmation.
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
    onChangeCount(Math.max(3, count - 1));
  };

  const handleIncrement = () => {
    onChangeCount(Math.min(20, count + 1));
  };

  return (
    <div style={{ display: 'grid', gap: '16px' }}>
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

      <p style={{ fontSize: '15px', color: 'var(--mute2)', lineHeight: 1.5, margin: 0 }}>
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
