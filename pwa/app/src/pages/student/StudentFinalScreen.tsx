import React from 'react';
import styles from './StudentView.module.css';

export interface StudentFinalScreenProps {
  score: number;
  questionCount?: number;
  username: string;
}

/**
 * End-of-game summary screen displaying individual score and celebratory message.
 *
 * @param {StudentFinalScreenProps} props - Component props containing student score, question count, and username.
 * @returns {JSX.Element} The rendered final score screen.
 */
export const StudentFinalScreen: React.FC<StudentFinalScreenProps> = ({
  score,
  questionCount = 0,
  username,
}) => {
  return (
    <section id="s-final" className={`${styles.section} ${styles.center}`}>
      <div className={styles.lbl}>TERMINÓ EL JUEGO</div>
      <div className={styles.score} id="finalScore">
        {score}
      </div>
      <p id="finalOf">respuestas correctas de {questionCount}</p>
      <h1 id="finalName">¡Buen trabajo, {username}!</h1>
    </section>
  );
};
