import React from 'react';
import { HoldButton } from '../../shared/ui/HoldButton/HoldButton';
import { HOLD_MEDIUM_MS } from '../../shared/ui/HoldButton/holdDurations';
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
 * The irreversible `Terminar la pregunta` CTA is a press-and-hold guard
 * (MEDIUM tier, see holdDurations); all other primary labels stay single-tap.
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
        {primaryText === 'Terminar la pregunta' ? (
          <HoldButton
            key="terminar"
            holdTime={HOLD_MEDIUM_MS}
            size="md"
            id="primary"
            ariaLabel="Terminar la pregunta"
            disabled={isPrimaryDisabled}
            backgroundColor="var(--p, #0B6E99)"
            fillColor="var(--navy, #062D3F)"
            textColor="#ffffff"
            fillTextColor="#ffffff"
            doneLabel="Cerrada"
            onHold={onPrimary}
          >
            Terminar la pregunta
          </HoldButton>
        ) : (
          <button
            id="primary"
            className={`${styles.primaryBtn} ${isLobbySuccess ? styles.ok : ''}`}
            disabled={isPrimaryDisabled}
            onClick={onPrimary}
          >
            {primaryText}
          </button>
        )}
      </div>
      <StepDots id="dots" count={3} currentIndex={wizardIndex} />
    </footer>
  );
};
