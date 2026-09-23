import React from 'react';
import { HoldButton } from '../../shared/ui/HoldButton/HoldButton';
import { HOLD_SHORT_MS } from '../../shared/ui/HoldButton/holdDurations';
import styles from './auth.module.css';
import type { PinFormModel } from './useAccountForms';

interface PinFormProps {
  form: PinFormModel;
  /** Disabled while the sibling username form is submitting. */
  disabled?: boolean;
}

/**
 * Voluntary PIN rotation form: current PIN plus double-entry of the new one,
 * submitted through the SHORT press-and-hold guard (see holdDurations).
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
      <HoldButton
        holdTime={HOLD_SHORT_MS}
        size="md"
        id="accChangePin"
        ariaLabel="Cambiar PIN"
        disabled={busy}
        doneLabel="PIN actualizado"
        onHold={() => void form.handlePinChange()}
      >
        Cambiar PIN
      </HoldButton>
      {form.pinError && (
        <div className={styles.errorBanner} id="accPinErr">
          {form.pinError}
        </div>
      )}
    </>
  );
};
