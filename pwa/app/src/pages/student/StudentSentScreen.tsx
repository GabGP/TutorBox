import React from 'react';
import { Timer } from 'lucide-react';
import styles from './StudentView.module.css';

export interface StudentSentScreenProps {
  myVote: string | null;
}

/**
 * Screen displayed while student awaits other votes or time elapsed.
 *
 * @param {StudentSentScreenProps} props - Component props containing the cast vote letter or null if timed out.
 * @returns {JSX.Element} The rendered waiting/sent screen.
 */
export const StudentSentScreen: React.FC<StudentSentScreenProps> = ({ myVote }) => {
  return (
    <section id="s-sent" className={`${styles.section} ${styles.center}`}>
      <div
        className={`${styles.pick} ${myVote ? styles[`k_${myVote}`] : ''}`}
        id="pick"
      >
        {myVote || <Timer size={40} aria-hidden />}
      </div>
      <h1 id="sentTitle">{myVote ? 'Respuesta enviada' : 'Se acabó el tiempo'}</h1>
      <p id="sentBody">
        {myVote ? 'Espera a que todos terminen.' : 'Espera el resultado de la pregunta.'}
      </p>
    </section>
  );
};
