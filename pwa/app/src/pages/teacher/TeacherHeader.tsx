import React from 'react';
import { ArrowLeft, BarChart3, Gamepad2, Settings } from 'lucide-react';
import { SpeechLanguage } from '../../features/speech/speech.types';
import utils from '../../shared/styles/utils.module.css';
import styles from './TeacherView.module.css';

export interface TeacherHeaderProps {
  title: string;
  subtitle: string;
  step: string;
  voiceLang: SpeechLanguage;
  onBack: () => void;
  onToggleVoice: () => void;
  onOpenSettings?: () => void;
  /** Opens the clicker fleet sheet; the button is hidden when absent. */
  onOpenClickers?: () => void;
  /** Opens the quiz / tutor / games reports sheet; hidden when absent. */
  onOpenReports?: () => void;
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
  onOpenClickers,
  onOpenReports,
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
        <ArrowLeft size={24} aria-hidden />
      </button>
      <div className={utils.grow}>
        <div className={styles.title} id="title">
          {title}
        </div>
        <div className={styles.subtitle} id="subtitle">
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
      {onOpenReports && (
        <button
          id="reportsBtn"
          onClick={onOpenReports}
          aria-label="Reportes"
          className={`${styles.voiceBtn} ${utils.rowInline}`}
        >
          <BarChart3 size={18} aria-hidden />
        </button>
      )}
      {onOpenClickers && (
        <button
          id="clickers"
          onClick={onOpenClickers}
          aria-label="Clickers"
          className={`${styles.voiceBtn} ${utils.rowInline}`}
        >
          <Gamepad2 size={18} aria-hidden />
        </button>
      )}
      {onOpenSettings && (
        <button
          id="settings"
          onClick={onOpenSettings}
          aria-label="Ajustes"
          className={`${styles.voiceBtn} ${utils.rowInline}`}
        >
          <Settings size={18} aria-hidden />
        </button>
      )}
    </header>
  );
};
