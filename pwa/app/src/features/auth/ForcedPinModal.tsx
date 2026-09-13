import React, { useState } from 'react';
import styles from './auth.module.css';

export interface ForcedPinModalProps {
  onPinChange: (newPin: string) => Promise<unknown>;
  currentPin?: string | null;
  title?: string;
  subtitle?: string;
}

/**
 * Forced PIN Rotation Modal component.
 * Prompts users flagged with `must_change_pin: true` to supply and confirm a new
 * non-default PIN before gaining full system access.
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
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const a = newPin.trim();
    const b = confirmPin.trim();

    if (!a || !b) {
      setError('Escribe y confirma tu nuevo PIN');
      return;
    }

    if (a !== b) {
      setError('Los dos PIN no coinciden');
      return;
    }

    if (currentPin && a === currentPin) {
      setError('El PIN nuevo debe ser diferente al temporal');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      await onPinChange(a);
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e.message || 'Error al cambiar PIN');
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

      {error && (
        <div className={styles.errorBanner} id="perr">
          {error}
        </div>
      )}

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
