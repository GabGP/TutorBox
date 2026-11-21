import React from 'react';
import { Download, MessageCircle, Trophy } from 'lucide-react';
import { Spinner } from '../../shared/ui/Spinner/Spinner';
import { ApplianceMode } from './modeApi';
import { TUTOR_LOADING_MESSAGE } from './tutorModelNotices';
import styles from './mode.module.css';

const OPTIONS: { mode: ApplianceMode; label: string; hint: string; Icon: typeof Trophy }[] = [
  { mode: 'quiz', label: 'Quiz', hint: 'Juego en clase', Icon: Trophy },
  { mode: 'tutor', label: 'Tutor', hint: 'Chat de práctica', Icon: MessageCircle },
  { mode: 'apps', label: 'Llevar a casa', hint: 'App para el teléfono', Icon: Download },
];

interface ModePickerProps {
  mode: ApplianceMode | null;
  saving: boolean;
  /** The mode being saved; the tutor card shows a spinner while its model loads. */
  pendingMode?: ApplianceMode | null;
  onChange: (mode: ApplianceMode) => void;
}

/**
 * The teacher's remote for the keyboard-less appliance: the class screen and every
 * student phone follow the mode picked here. A failed switch floats as an error toast
 * from the teacher view.
 *
 * @param {ModePickerProps} props - Current mode, saving flag, pending mode and change handler.
 * @returns {JSX.Element} Three large mode buttons.
 */
export const ModePicker: React.FC<ModePickerProps> = ({ mode, saving, pendingMode = null, onChange }) => (
  <section className={styles.picker} aria-label="Modo de la clase">
    <div className={styles.options} role="group">
      {OPTIONS.map(({ mode: value, label, hint, Icon }) => {
        const loadingTutor = value === 'tutor' && pendingMode === 'tutor';
        return (
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
            {loadingTutor ? (
              <span className={styles.loading}>
                <Spinner label={TUTOR_LOADING_MESSAGE} size={12} />
                {TUTOR_LOADING_MESSAGE}
              </span>
            ) : (
              <span>{hint}</span>
            )}
          </button>
        );
      })}
    </div>
  </section>
);
