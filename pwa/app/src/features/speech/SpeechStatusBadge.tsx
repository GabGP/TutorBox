import React from 'react';
import { SpeechState } from './speech.types';
import styles from './SpeechStatusBadge.module.css';

export interface SpeechStatusBadgeProps {
  state: SpeechState;
  message: string;
  id?: string;
}

/**
 * Offline Text-to-Speech Status Badge with animated equalizer and synthesis spinner.
 */
export const SpeechStatusBadge: React.FC<SpeechStatusBadgeProps> = ({
  state,
  message,
  id = 'speechState',
}) => {
  if (!message) return null;

  const isPlaying = state === 'playing';
  const isError = state === 'error';
  const isLoading = state === 'loading';
  const isDone = state === 'done';

  const stateClass = isLoading
    ? styles.loading
    : isPlaying
    ? styles.playing
    : isDone
    ? styles.done
    : isError
    ? styles.error
    : '';

  return (
    <div
      id={id}
      className={`voice ${isPlaying ? 'on' : ''} ${isError ? 'bad' : ''} ${styles.badge} ${stateClass}`}
    >
      <div className={styles.iconBox} aria-hidden="true">
        {isLoading ? (
          <div className={styles.spinner} />
        ) : isPlaying ? (
          <div className={styles.wave}>
            <span className={styles.bar} />
            <span className={styles.bar} />
            <span className={styles.bar} />
          </div>
        ) : isDone ? (
          <span>✓</span>
        ) : (
          <span className={styles.pip} />
        )}
      </div>
      <span>{message}</span>
    </div>
  );
};
