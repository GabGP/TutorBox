import React from 'react';
import styles from './PlayButton.module.css';

export type PlayPhase = 'idle' | 'loading' | 'playing' | 'done';

export interface PlayButtonProps {
  phase: PlayPhase;
  onClick: () => void;
  disabled?: boolean;
  id?: string;
  ariaLabel?: string;
  /** Idle/done content: plain label or icon + label. */
  idleLabel: React.ReactNode;
  loadingLabel?: string;
  playingLabel?: string;
  doneLabel?: React.ReactNode;
}

/**
 * Shared speech play button with loading spinner and playing equalizer states.
 * Single owner of the playBtn/btnSpinner/btnWave idiom previously copied
 * between RemediationAlert and VoicePicker.
 */
export const PlayButton: React.FC<PlayButtonProps> = ({
  phase,
  onClick,
  disabled = false,
  id,
  ariaLabel,
  idleLabel,
  loadingLabel = 'Preparando la voz…',
  playingLabel = 'Leyendo…',
  doneLabel,
}) => {
  const isPlaying = phase === 'playing';
  const label =
    phase === 'loading'
      ? loadingLabel
      : isPlaying
        ? playingLabel
        : phase === 'done' && doneLabel !== undefined
          ? doneLabel
          : idleLabel;

  return (
    <button
      type="button"
      id={id}
      className={`${styles.playBtn} ${isPlaying ? styles.playBtnActive : ''}`}
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel}
    >
      {phase === 'loading' && (
        <span className={styles.btnSpinner} aria-hidden="true" />
      )}
      {isPlaying && (
        <span className={styles.btnWave} aria-hidden="true">
          <span className={styles.btnBar} />
          <span className={styles.btnBar} />
          <span className={styles.btnBar} />
        </span>
      )}
      <span className={styles.btnLabel}>{label}</span>
    </button>
  );
};

/** Inline spinner for non-play buttons (e.g. admin load actions). */
export const BtnSpinner: React.FC = () => (
  <span className={styles.btnSpinner} aria-hidden="true" />
);
