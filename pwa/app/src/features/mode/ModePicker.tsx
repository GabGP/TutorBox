import React from 'react';
import { Download, MessageCircle, Trophy } from 'lucide-react';
import { ApplianceMode } from './modeApi';
import styles from './mode.module.css';

const OPTIONS: { mode: ApplianceMode; label: string; hint: string; Icon: typeof Trophy }[] = [
  { mode: 'quiz', label: 'Quiz', hint: 'Juego en clase', Icon: Trophy },
  { mode: 'tutor', label: 'Tutor', hint: 'Chat de práctica', Icon: MessageCircle },
  { mode: 'apps', label: 'Llevar a casa', hint: 'App para el teléfono', Icon: Download },
];

interface ModePickerProps {
  mode: ApplianceMode | null;
  saving: boolean;
  error: string | null;
  onChange: (mode: ApplianceMode) => void;
}

/**
 * The teacher's remote for the keyboard-less appliance: the class screen and every
 * student phone follow the mode picked here.
 *
 * @param {ModePickerProps} props - Current mode, saving flag, last error and change handler.
 * @returns {JSX.Element} Three large mode buttons.
 */
export const ModePicker: React.FC<ModePickerProps> = ({ mode, saving, error, onChange }) => (
  <section className={styles.picker} aria-label="Modo de la clase">
    <div className={styles.options} role="group">
      {OPTIONS.map(({ mode: value, label, hint, Icon }) => (
        <button
          key={value}
          type="button"
          className={styles.option}
          aria-pressed={(mode ?? 'quiz') === value}
          disabled={saving}
          onClick={() => onChange(value)}
        >
          <Icon size={26} aria-hidden />
          <strong>{label}</strong>
          <span>{hint}</span>
        </button>
      ))}
    </div>
    {error && (
      <p className={styles.error} role="alert">
        {error}
      </p>
    )}
  </section>
);
