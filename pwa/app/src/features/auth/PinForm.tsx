import React from 'react';
import styles from './auth.module.css';
import type { PinFormModel } from './useAccountForms';

interface PinFormProps {
  form: PinFormModel;
  /** Disabled while the sibling username form is submitting. */
  disabled?: boolean;
}

/**
 * Voluntary PIN rotation form: current PIN plus double-entry of the new one.
 */
export const PinForm: React.FC<PinFormProps> = ({ form, disabled = false }) => {
  const busy = form.busy || disabled;
  return (
    <>
      <input
        id="accPinCurrent"
        type="password"
        inputMode="numeric"
        maxLength={8}
        autoComplete="current-password"
        placeholder="PIN actual (para cambiar PIN)"
        className={styles.inputField}
        value={form.pinCurrent}
        onChange={(e) => form.setPinCurrent(e.target.value)}
        disabled={busy}
      />
      <input
        id="accNewPin"
        type="password"
        inputMode="numeric"
        maxLength={8}
        autoComplete="new-password"
        placeholder="PIN nuevo (4 a 8 números)"
        className={styles.inputField}
        value={form.newPin}
        onChange={(e) => form.setNewPin(e.target.value)}
        disabled={busy}
      />
      <input
        id="accNewPin2"
        type="password"
        inputMode="numeric"
        maxLength={8}
        autoComplete="new-password"
        placeholder="Repite el PIN nuevo"
        className={styles.inputField}
        value={form.confirmPin}
        onChange={(e) => form.setConfirmPin(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') form.handlePinChange();
        }}
        disabled={busy}
      />
      <button
        type="button"
        id="accChangePin"
        className={styles.submitBtn}
        onClick={form.handlePinChange}
        disabled={busy}
      >
        Cambiar PIN
      </button>
      {form.pinError && (
        <div className={styles.errorBanner} id="accPinErr">
          {form.pinError}
        </div>
      )}
    </>
  );
};
