import React from 'react';
import styles from './StartCountdown.module.css';
import { useStartCountdown } from './useStartCountdown';

export interface StartCountdownProps {
  /** round.starts_in from the session state; null or 0 shows nothing. */
  startsIn: number | null | undefined;
}

/**
 * Full-screen 3-2-1 before a game's first question, on the teacher's phone, the students'
 * phones and the classroom screen. It covers the page, so nobody can vote before the
 * server opens the round (a vote that early gets 409 anyway).
 */
export const StartCountdown: React.FC<StartCountdownProps> = ({ startsIn }) => {
  const secondsLeft = useStartCountdown(startsIn);
  if (secondsLeft === null) return null;
  return (
    <div className={styles.overlay} role="timer" aria-live="assertive" aria-label={`El juego empieza en ${secondsLeft}`}>
      <p className={styles.title} aria-hidden="true">
        ¡Prepárense!
      </p>
      <span key={secondsLeft} className={styles.digit} aria-hidden="true">
        {secondsLeft}
      </span>
      <p className={styles.caption} aria-hidden="true">
        El juego empieza en…
      </p>
    </div>
  );
};
