import React from 'react';
import { HoldButton } from '../../shared/ui/HoldButton/HoldButton';
import styles from './auth.module.css';
import type { UsernameFormModel } from './useAccountForms';

interface UsernameFormProps {
  form: UsernameFormModel;
  /** Disabled while the sibling PIN form is submitting. */
  disabled?: boolean;
}

/**
 * Self username rename form: current-PIN gate plus HoldButton
 * press-and-hold, since renaming your own account ends the session.
 */
export const UsernameForm: React.FC<UsernameFormProps> = ({ form, disabled = false }) => {
  const busy = form.busy || disabled;
  return (
    <>
      <div className={styles.sectionLabel}>Tu nombre de usuario</div>
      <div className={styles.hint}>
        Cambia el nombre de TU cuenta (no crea una cuenta nueva) y
        deberás iniciar sesión de nuevo. Para crear una cuenta para
        otra persona usa Usuarios → Usuario nuevo.
      </div>
      <input
        id="accNamePin"
        type="password"
        inputMode="numeric"
        maxLength={8}
        autoComplete="current-password"
        placeholder="PIN actual (para cambiar nombre)"
        className={styles.inputField}
        value={form.namePin}
        onChange={(e) => form.setNamePin(e.target.value)}
        disabled={busy}
      />
      <input
        id="accNewUser"
        className={styles.inputField}
        maxLength={32}
        autoComplete="username"
        placeholder="Nombre nuevo"
        value={form.newUsername}
        onChange={(e) => form.setNewUsername(e.target.value)}
        disabled={busy}
      />
      <HoldButton
        holdTime={2000}
        size="md"
        id="accChangeUser"
        ariaLabel="Cambiar mi nombre"
        disabled={busy}
        onHold={() => void form.handleUsernameChange()}
      >
        Cambiar mi nombre
      </HoldButton>
      {form.nameError && (
        <div className={styles.errorBanner} id="accNameErr">
          {form.nameError}
        </div>
      )}
    </>
  );
};
