import React from 'react';
import { SpeechStatusBadge } from '../speech/SpeechStatusBadge';
import { SpeechLanguage, SpeechState } from '../speech/speech.types';
import styles from './report.module.css';

export interface RemediationAlertProps {
  shouldShow: boolean;
  dominantCount: number;
  totalVotes: number;
  dominantPercentage: number;
  dominantOptionText: string;
  explanation: string;
  speechState: SpeechState;
  speechMessage: string;
  voiceLang: SpeechLanguage;
  onPlay: () => void;
  onSkip: () => void;
}

/**
 * Pedagogical Remediation Alert component.
 * Renders prominent visual and auditory remediation controls whenever a diagnostic distractor
 * exceeds the >51% threshold, providing audio synthesis triggers and pedagogical explanations.
 *
 * @param {RemediationAlertProps} props - Component props containing distractor stats, explanation, and audio state.
 * @returns {JSX.Element | null} The rendered remediation banner or null if threshold is not met.
 */
export const RemediationAlert: React.FC<RemediationAlertProps> = ({
  shouldShow,
  dominantCount,
  totalVotes,
  dominantPercentage,
  dominantOptionText,
  explanation,
  speechState,
  speechMessage,
  voiceLang,
  onPlay,
  onSkip,
}) => {
  if (!shouldShow) return null;

  const defaultVoiceLabel =
    voiceLang === 'es' ? 'Escuchar en español' : "Escuchar en k'iche'";

  const playLabel =
    speechState === 'loading'
      ? 'Preparando la voz…'
      : speechState === 'playing'
      ? 'Leyendo…'
      : speechState === 'done'
      ? 'Escuchar otra vez'
      : defaultVoiceLabel;

  const skipLabel =
    speechState === 'loading' || speechState === 'playing' ? 'Detener' : 'Saltar';

  const isBusy = speechState === 'loading' || speechState === 'playing';

  return (
    <div className={styles.alertLg} id="ralert">
      <b id="ralertTitle">
        {dominantCount} de {totalVotes} ({Math.round(dominantPercentage)}%) eligieron {dominantOptionText}
      </b>
      <div id="explain">{explanation}</div>

      <SpeechStatusBadge state={speechState} message={speechMessage} />

      <div className={styles.btns}>
        <button
          type="button"
          id="play"
          className={styles.playBtn}
          onClick={onPlay}
          disabled={isBusy}
        >
          {playLabel}
        </button>
        <button
          type="button"
          id="skip"
          className={styles.skipBtn}
          onClick={onSkip}
        >
          {skipLabel}
        </button>
      </div>
    </div>
  );
};
