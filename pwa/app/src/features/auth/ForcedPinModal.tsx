import React, { useState } from 'react';
import { toErrorMessage } from '../../shared/lib/errors';
import { ToastViewport } from '../../shared/ui/Toast/ToastViewport';
import { useToastQueue } from '../../shared/ui/Toast/useToastQueue';
import styles from './auth.module.css';
import { validatePinPair } from './pinValidation';

export interface ForcedPinModalProps {
  onPinChange: (newPin: string) => Promise<unknown>;
  currentPin?: string | null;
  title?: string;
  subtitle?: string;
}

/**
 * Forced PIN Rotation Modal component.
 * Prompts users flagged with `must_change_pin: true` to supply and confirm a new
 * non-default PIN before gaining full system access. Failures float as error
 * toasts so the card never shifts layout.
 *
 * @param {ForcedPinModalProps} props - Component props containing the rotation callback and titles.
 * @returns {JSX.Element} The rendered forced PIN rotation form card.
 */
export const ForcedPinModal: React.FC<ForcedPinModalProps> = ({
  onPinChange,
  currentPin,
  title = 'Elige tu PIN nuevo',
  subtitle = 'Tu maestro te dio un PIN temporal. Cámbialo por uno que solo tú sepas.',
}) => {
  const [newPin, setNewPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const { toasts, pushToast, dismissToast } = useToastQueue();

  const fail = (message: string) =>
    pushToast({ message, tone: 'error' });

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const a = newPin.trim();
    const b = confirmPin.trim();

    const pairError = validatePinPair(a, b, currentPin);
    if (pairError) {
      fail(
        pairError === 'empty'
          ? 'Escribe y confirma tu nuevo PIN'
          : pairError === 'mismatch'
            ? 'Los dos PIN no coinciden'
            : 'El PIN nuevo debe ser diferente al temporal'
      );
      return;
    }

    setSubmitting(true);

    try {
      await onPinChange(a);
    } catch (err: unknown) {
      fail(toErrorMessage(err, 'Error al cambiar PIN'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className={styles.authCard} id="s-pin">
      <div className={styles.logo}>T</div>
      <div className={styles.titleBlock}>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>

      <input
        id="npin"
        type="password"
        inputMode="numeric"
        maxLength={8}
        placeholder="PIN nuevo (4 a 8 números)"
        className={styles.inputField}
        value={newPin}
        onChange={(e) => setNewPin(e.target.value)}
        disabled={submitting}
      />

      <input
        id="npin2"
        type="password"
        inputMode="numeric"
        maxLength={8}
        placeholder="Repite el PIN nuevo"
        className={styles.inputField}
        value={confirmPin}
        onChange={(e) => setConfirmPin(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') handleSubmit();
        }}
        disabled={submitting}
      />

      <ToastViewport toasts={toasts} onDismiss={(id) => dismissToast(id)} />

      <button
        type="button"
        id="setpin"
        className={styles.submitBtn}
        onClick={() => handleSubmit()}
        disabled={submitting}
      >
        Guardar y entrar
      </button>
    </section>
  );
};
