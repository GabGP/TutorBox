import React from 'react';
import { StepDots } from '../../shared/ui/StepDots/StepDots';
import styles from './TeacherView.module.css';

export interface TeacherFooterProps {
  primaryText: string;
  secondaryText?: string;
  isPrimaryDisabled: boolean;
  isLobbySuccess: boolean;
  wizardIndex: number;
  onPrimary: () => void;
  onSecondary: () => void;
}

/**
 * Teacher Console Bottom Action Bar and Wizard Progress.
 * Renders the primary action CTA, secondary navigation/reset button, and wizard step dots.
 *
 * @param {TeacherFooterProps} props - Component props containing action button labels, disabled states, and callbacks.
 * @returns {JSX.Element} The rendered teacher console footer.
 */
export const TeacherFooter: React.FC<TeacherFooterProps> = ({
  primaryText,
  secondaryText,
  isPrimaryDisabled,
  isLobbySuccess,
  wizardIndex,
  onPrimary,
  onSecondary,
}) => {
  return (
    <footer className={styles.footer}>
      <div className={styles.btns}>
        {secondaryText && (
          <button
            id="secondary"
            className={styles.secondaryBtn}
            onClick={onSecondary}
          >
            {secondaryText}
          </button>
        )}
        <button
          id="primary"
          className={`${styles.primaryBtn} ${isLobbySuccess ? styles.ok : ''}`}
          disabled={isPrimaryDisabled}
          onClick={onPrimary}
        >
          {primaryText}
        </button>
      </div>
      <StepDots id="dots" count={3} currentIndex={wizardIndex} />
    </footer>
  );
};
