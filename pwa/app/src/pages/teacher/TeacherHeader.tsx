import React from 'react';
import { SpeechLanguage } from '../../features/speech/speech.types';
import styles from './TeacherView.module.css';

export interface TeacherHeaderProps {
  title: string;
  subtitle: string;
  step: string;
  voiceLang: SpeechLanguage;
  onBack: () => void;
  onToggleVoice: () => void;
  onOpenSettings?: () => void;
}

/**
 * Teacher Console Top Navigation Bar.
 * Renders back navigation button, current screen title/step subtitle, and offline language toggle.
 *
 * @param {TeacherHeaderProps} props - Component props containing titles, language state, and event callbacks.
 * @returns {JSX.Element} The rendered teacher console header.
 */
export const TeacherHeader: React.FC<TeacherHeaderProps> = ({
  title,
  subtitle,
  step,
  voiceLang,
  onBack,
  onToggleVoice,
  onOpenSettings,
}) => {
  return (
    <header className={styles.header}>
      <button
        id="back"
        className={styles.backBtn}
        disabled={step !== 'count'}
        onClick={onBack}
        aria-label="Volver"
      >
        ←
      </button>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: '19px', fontWeight: 600 }} id="title">
          {title}
        </div>
        <div style={{ fontSize: '13px', color: 'var(--mute2)' }} id="subtitle">
          {subtitle}
        </div>
      </div>
      <button
        id="voice"
        className={styles.voiceBtn}
        onClick={onToggleVoice}
      >
        {voiceLang === 'es' ? 'Voz ES' : "Voz K'iche'"}
      </button>
      {onOpenSettings && (
        <button
          id="settings"
          className={styles.voiceBtn}
          onClick={onOpenSettings}
          aria-label="Ajustes"
        >
          ⚙
        </button>
      )}
    </header>
  );
};
