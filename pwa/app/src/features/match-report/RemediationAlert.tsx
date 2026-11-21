import React from 'react';
import { TriangleAlert } from 'lucide-react';
import { PlayButton } from '../../shared/ui/PlayButton/PlayButton';
import { SpeechLanguage, SpeechState } from '../speech/speech.types';
import { SPEECH_LANGUAGE_NAMES } from '../speech/speechLanguages';
import styles from './report.module.css';

export interface RemediationAlertProps {
  shouldShow: boolean;
  dominantCount: number;
  totalVotes: number;
  dominantPercentage: number;
  dominantOptionText: string;
  explanation: string;
  speechState: SpeechState;
  voiceLang: SpeechLanguage;
  onPlay: () => void;
  onSkip: () => void;
}

/**
 * Pedagogical Remediation Alert component.
 * Displays diagnostic distractor error statistics, explanation, and interactive TTS audio controls.
 */
export const RemediationAlert: React.FC<RemediationAlertProps> = ({
  shouldShow,
  dominantCount,
  totalVotes,
  dominantPercentage,
  dominantOptionText,
  explanation,
  speechState,
  voiceLang,
  onPlay,
  onSkip,
}) => {
  if (!shouldShow) return null;

  const defaultVoiceLabel = `Escuchar en ${SPEECH_LANGUAGE_NAMES[voiceLang]}`;

  const isBusy = speechState === 'loading' || speechState === 'playing';

  const handlePrimaryClick = () => {
    if (isBusy) {
      onSkip();
    } else {
      onPlay();
    }
  };

  const speechPhase =
    speechState === 'loading' || speechState === 'playing' || speechState === 'done'
      ? speechState
      : ('idle' as const);

  return (
    <div className={styles.alertLg} id="ralert">
      <div className={styles.remediationTagRow}>
        <span className={styles.remediationTag}><TriangleAlert size={13} aria-hidden /> Error conceptual mayoritario (&gt;51%)</span>
      </div>

      <b id="ralertTitle">
        {dominantCount} de {totalVotes} ({Math.round(dominantPercentage)}%) eligieron {dominantOptionText}
      </b>

      <div id="explain" className={styles.explanationBox}>
        {explanation}
      </div>

      <div className={styles.btns}>
        <PlayButton
          phase={speechPhase}
          onClick={handlePrimaryClick}
          id="play"
          ariaLabel={
            speechState === 'loading'
              ? 'Preparando la voz, clic para cancelar'
              : speechState === 'playing'
              ? 'Leyendo explicación, clic para detener'
              : defaultVoiceLabel
          }
          idleLabel={defaultVoiceLabel}
          doneLabel="Escuchar otra vez"
        />
        <button
          type="button"
          id="skip"
          className={styles.skipBtn}
          onClick={onSkip}
        >
          {isBusy ? 'Detener' : 'Saltar'}
        </button>
      </div>
    </div>
  );
};
