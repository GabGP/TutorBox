import React from 'react';
import { SpeechState } from './speech.types';

export interface SpeechStatusBadgeProps {
  state: SpeechState;
  message: string;
  id?: string;
}

/**
 * Offline Text-to-Speech Status Badge.
 * Visual feedback indicator displaying the synthesis lifecycle state (idle, loading,
 * playing, finished, or error) with an animated color status pip.
 *
 * @param {SpeechStatusBadgeProps} props - Component props containing speech state and descriptive message.
 * @returns {JSX.Element | null} The rendered badge or null if message is empty.
 */
export const SpeechStatusBadge: React.FC<SpeechStatusBadgeProps> = ({
  state,
  message,
  id = 'speechState',
}) => {
  if (!message) {
    return null;
  }

  const isPlaying = state === 'playing';
  const isError = state === 'error';

  return (
    <div
      id={id}
      className={`voice ${isPlaying ? 'on' : ''} ${isError ? 'bad' : ''}`}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '9px',
        fontSize: '14px',
        fontWeight: 600,
        color: isError ? 'var(--bad-ink)' : 'var(--warn)',
      }}
    >
      <i
        style={{
          width: '10px',
          height: '10px',
          flex: '0 0 10px',
          borderRadius: '50%',
          background: isPlaying ? 'var(--D)' : isError ? 'var(--bad)' : 'var(--warn)',
        }}
      />
      <span>{message}</span>
    </div>
  );
};
