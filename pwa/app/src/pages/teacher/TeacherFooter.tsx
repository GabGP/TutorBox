import React from 'react';
import { HoldButton } from '../../shared/ui/HoldButton/HoldButton';
import { HOLD_LONG_MS, HOLD_MEDIUM_MS } from '../../shared/ui/HoldButton/holdDurations';
import { StepDots } from '../../shared/ui/StepDots/StepDots';
import styles from './TeacherView.module.css';

export interface TeacherFooterProps {
  primaryText: string;
  secondaryText?: string;
  /** The secondary action ends the match (Cancelar mid-game): hold to confirm. */
  isSecondaryHold?: boolean;
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
 * Cancelar during a started match ends it for everyone, so it is a LONG hold.
 */
export const TeacherFooter: React.FC<TeacherFooterProps> = ({
  primaryText,
  secondaryText,
  isSecondaryHold = false,
  isPrimaryDisabled,
  isLobbySuccess,
  wizardIndex,
  onPrimary,
  onSecondary,
}) => {
  return (
    <footer className={styles.footer}>
      <div className={styles.btns}>
        {secondaryText && isSecondaryHold && (
          <HoldButton
            key="cancelar-juego"
            holdTime={HOLD_LONG_MS}
            size="md"
            radius={32}
            id="secondary"
            className={styles.secondaryHold}
            ariaLabel={`Mantén para ${secondaryText.toLowerCase()} el juego`}
            backgroundColor="#ffffff"
            fillColor="var(--bad, #B3261E)"
            textColor="var(--ink2, #3b4a43)"
            fillTextColor="#ffffff"
            doneLabel="Cancelado"
            onHold={onSecondary}
          >
            {secondaryText}
          </HoldButton>
        )}
        {secondaryText && !isSecondaryHold && (
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
            backgroundColor="var(--p, #1F3E33)"
            fillColor="var(--accent, #F5B3B3)"
            textColor="#ffffff"
            fillTextColor="var(--accent-ink, #1F3E33)"
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
