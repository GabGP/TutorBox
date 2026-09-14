import React from 'react';
import { ConfettiCanvas } from '../../shared/ui/Confetti/ConfettiCanvas';
import styles from './StudentResultScreen.module.css';

export interface StudentResultScreenProps {
  isHit: boolean;
  myVote: string | null;
  answer: string;
  why?: string;
  score: number;
  roundIndex: number;
}

/**
 * Individual Student Round Result Screen.
 * Displays immediate personal feedback (check/cross glyph, correct answer text,
 * pedagogical explanation, and current cumulative score).
 * Triggers confetti animation on correct answers.
 *
 * @param {StudentResultScreenProps} props - Component props containing correctness flag, user vote, and cumulative score.
 * @returns {JSX.Element} The rendered student round outcome screen.
 */
export const StudentResultScreen: React.FC<StudentResultScreenProps> = ({
  isHit,
  myVote,
  answer,
  why,
  score,
  roundIndex,
}) => {
  return (
    <section id="s-result" className={`${styles.section} ${styles.center}`}>
      <ConfettiCanvas active={isHit} />
      <div className={`${styles.glyph} ${isHit ? styles.glyphHit : ''}`} id="glyph">
        {isHit ? '✓' : myVote ? '✕' : '–'}
      </div>
      <h1 id="resultTitle">{isHit ? '¡Correcto!' : myVote ? 'Casi' : 'Sin respuesta'}</h1>
      <p id="resultBody">{isHit ? answer : `La respuesta era ${answer}`}</p>
      {why && (
        <div className={styles.explain} id="explain">
          {why}
        </div>
      )}
      <div className={styles.chip} id="chip">
        {score} de {roundIndex + 1} correctas
      </div>
    </section>
  );
};
