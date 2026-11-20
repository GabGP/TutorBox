import React from 'react';
import { ArrowLeft, BarChart3, Gamepad2, Settings } from 'lucide-react';
import utils from '../../shared/styles/utils.module.css';
import styles from './TeacherView.module.css';

export interface TeacherHeaderProps {
  title: string;
  subtitle: string;
  /** The back arrow works (bank pick, lobby); otherwise its place stays empty. */
  canGoBack: boolean;
  onBack: () => void;
  onOpenSettings?: () => void;
  /** Opens the clicker fleet sheet; the button is hidden when absent. */
  onOpenClickers?: () => void;
  /** Opens the quiz / tutor / games reports sheet; hidden when absent. */
  onOpenReports?: () => void;
}

/**
 * Teacher Console Top Navigation Bar.
 * The same bar in every mode and step: a fixed height, the back arrow's place
 * always kept (empty when there is nowhere to go back), a one-line title and
 * subtitle that end in … when too long, and round icon buttons of one size.
 * The quiz voice language lives in Ajustes → Voz.
 *
 * @param {TeacherHeaderProps} props - Titles, whether back works, and the sheet openers.
 * @returns {JSX.Element} The rendered teacher console header.
 */
export const TeacherHeader: React.FC<TeacherHeaderProps> = ({
  title,
  subtitle,
  canGoBack,
  onBack,
  onOpenSettings,
  onOpenClickers,
  onOpenReports,
}) => {
  return (
    <header className={styles.header}>
      <button
        id="back"
        className={styles.backBtn}
        disabled={!canGoBack}
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
      {onOpenReports && (
        <button id="reportsBtn" onClick={onOpenReports} aria-label="Reportes" className={styles.iconBtn}>
          <BarChart3 size={18} aria-hidden />
        </button>
      )}
      {onOpenClickers && (
        <button id="clickers" onClick={onOpenClickers} aria-label="Clickers" className={styles.iconBtn}>
          <Gamepad2 size={18} aria-hidden />
        </button>
      )}
      {onOpenSettings && (
        <button id="settings" onClick={onOpenSettings} aria-label="Ajustes" className={styles.iconBtn}>
          <Settings size={18} aria-hidden />
        </button>
      )}
    </header>
  );
};
