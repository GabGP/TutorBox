import React from 'react';
import { TriangleAlert } from 'lucide-react';
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
  speechMessage?: string;
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
  speechMessage,
  voiceLang,
  onPlay,
  onSkip,
}) => {
  if (!shouldShow) return null;

  const defaultVoiceLabel =
    voiceLang === 'es' ? 'Escuchar en español' : "Escuchar en k'iche'";

  const isBusy = speechState === 'loading' || speechState === 'playing';

  const handlePrimaryClick = () => {
    if (isBusy) {
      onSkip();
    } else {
      onPlay();
    }
  };

  return (
    <div className={styles.alertLg} id="ralert">
      <div className={styles.remediationTagRow}>
        <span className={styles.remediationTag} style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}><TriangleAlert size={13} aria-hidden /> Error conceptual mayoritario (&gt;51%)</span>
      </div>

      <b id="ralertTitle">
        {dominantCount} de {totalVotes} ({Math.round(dominantPercentage)}%) eligieron {dominantOptionText}
      </b>

      <div id="explain" className={styles.explanationBox}>
        {explanation}
      </div>

      <div className={styles.btns}>
        <button
          type="button"
          id="play"
          className={`${styles.playBtn} ${speechState === 'playing' ? styles.playBtnActive : ''}`}
          onClick={handlePrimaryClick}
          aria-label={
            speechState === 'loading'
              ? 'Preparando la voz, clic para cancelar'
              : speechState === 'playing'
              ? 'Leyendo explicación, clic para detener'
              : defaultVoiceLabel
          }
        >
          {speechState === 'loading' && (
            <span className={styles.btnSpinner} aria-hidden="true" />
          )}
          {speechState === 'playing' && (
            <span className={styles.btnWave} aria-hidden="true">
              <span className={styles.btnBar} />
              <span className={styles.btnBar} />
              <span className={styles.btnBar} />
            </span>
          )}
          <span>
            {speechState === 'loading'
              ? 'Preparando la voz…'
              : speechState === 'playing'
              ? 'Leyendo…'
              : speechState === 'done'
              ? 'Escuchar otra vez'
              : defaultVoiceLabel}
          </span>
        </button>
        <button
          type="button"
          id="skip"
          className={styles.skipBtn}
          onClick={onSkip}
        >
          {isBusy ? 'Detener' : 'Saltar'}
        </button>
      </div>
      {speechMessage && (
        <div id="speechState" role="status" aria-live="polite">
          {speechMessage}
        </div>
      )}
    </div>
  );
};
