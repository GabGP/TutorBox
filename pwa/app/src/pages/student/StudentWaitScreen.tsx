import React from 'react';
import styles from './StudentView.module.css';

export interface StudentWaitScreenProps {
  username: string;
}

/**
 * Pre-game student waiting screen with animated avatar bubble.
 *
 * @param {StudentWaitScreenProps} props - Component props containing the logged-in student username.
 * @returns {JSX.Element} The rendered student waiting screen.
 */
export const StudentWaitScreen: React.FC<StudentWaitScreenProps> = ({ username }) => {
  return (
    <section id="s-wait" className={`${styles.section} ${styles.center}`}>
      <div className={styles.bubble} id="initial">
        {username.charAt(0).toUpperCase()}
      </div>
      <h1 id="waitTitle">Hola, {username}</h1>
      <p>Tu maestro está preparando el juego.</p>
    </section>
  );
};
