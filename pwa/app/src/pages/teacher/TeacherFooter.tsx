import React, { useRef } from 'react';
import { HoldButton } from '../../shared/ui/HoldButton/HoldButton';
import { HOLD_LONG_MS, HOLD_MEDIUM_MS } from '../../shared/ui/HoldButton/holdDurations';
import { StepDots } from '../../shared/ui/StepDots/StepDots';
import { useToastDock } from '../../shared/ui/Toast/useToastDock';
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
  /** A hold button was only tapped: the parent says how to use it. */
  onHoldTap?: (hint: string) => void;
}

const TERMINAR_HINT = 'Mantén presionado para terminar la pregunta.';
const CANCELAR_HINT = 'Mantén presionado para cancelar el juego.';

/**
 * Teacher Console Bottom Action Bar and Wizard Progress.
 * Renders the primary action CTA, secondary navigation/reset button, and wizard step dots.
 * The irreversible `Terminar la pregunta` CTA is a press-and-hold guard
 * (MEDIUM tier, see holdDurations); all other primary labels stay single-tap.
 * Cancelar during a started match ends it for everyone, so it is a LONG hold.
 * Both holds keep the footer's pill shape, Cancelar on the left, so they read
 * as one pair. Toasts float above the footer instead of covering it. A tap
 * on either hold asks the parent to explain that it needs a hold.
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
  onHoldTap,
}) => {
  const footerRef = useRef<HTMLElement>(null);
  useToastDock(footerRef);
  return (
    <footer className={styles.footer} ref={footerRef}>
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
            onTap={() => onHoldTap?.(CANCELAR_HINT)}
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
            radius={32}
            id="primary"
            className={styles.primaryHold}
            ariaLabel="Terminar la pregunta"
            disabled={isPrimaryDisabled}
            backgroundColor="var(--p, #1F3E33)"
            fillColor="var(--accent, #F5B3B3)"
            textColor="#ffffff"
            fillTextColor="var(--accent-ink, #1F3E33)"
            doneLabel="Cerrada"
            onHold={onPrimary}
            onTap={() => onHoldTap?.(TERMINAR_HINT)}
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
