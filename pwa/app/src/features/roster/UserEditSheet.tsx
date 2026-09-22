import React, { useEffect, useState } from 'react';
import { getRoleLabel } from '../../shared/constants/roles';
import { toErrorMessage } from '../../shared/lib/errors';
import formStyles from '../../shared/styles/forms.module.css';
import { HoldButton } from '../../shared/ui/HoldButton/HoldButton';
import { Sheet } from '../../shared/ui/Sheet/Sheet';
import styles from './roster.module.css';
import { RosterStudent } from './roster.types';

export interface UserEditSheetProps {
  /** Null = closed. */
  user: RosterStudent | null;
  onClose: () => void;
  onResetPin: (id: string, username: string) => Promise<unknown>;
  onDeleteUser?: (id: string, username: string) => Promise<unknown>;
  /** Roles the caller may assign; sheet hides role editing when absent. */
  editableRoles?: string[];
  onRoleChange?: (id: string, role: string) => Promise<unknown>;
}

/**
 * Edit card for a roster user. Role edits are staged locally and applied
 * with Guardar cambios (guards against locking out the last manager
 * server-side); PIN reset and delete act immediately. Actions not provided
 * by the parent are hidden (e.g. lobby offers reset only).
 */
export const UserEditSheet: React.FC<UserEditSheetProps> = ({
  user,
  onClose,
  onResetPin,
  onDeleteUser,
  editableRoles,
  onRoleChange,
}) => {
  const [busy, setBusy] = useState(false);
  const [roleError, setRoleError] = useState('');
  const [pendingRole, setPendingRole] = useState('');

  useEffect(() => {
    setBusy(false);
    setRoleError('');
    setPendingRole(user?.role || '');
  }, [user?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!user) return null;

  const roleDirty = Boolean(pendingRole) && pendingRole !== user.role;

  const handleSaveRole = async () => {
    if (!onRoleChange || !roleDirty) return;
    setBusy(true);
    setRoleError('');
    try {
      await onRoleChange(user.id, pendingRole);
      onClose();
    } catch (err: unknown) {
      setRoleError(toErrorMessage(err, 'Error al cambiar rol'));
    } finally {
      setBusy(false);
    }
  };

  const handleReset = async () => {
    setBusy(true);
    try {
      await onResetPin(user.id, user.username);
      onClose();
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async () => {
    setBusy(true);
    try {
      await onDeleteUser?.(user.id, user.username);
      onClose();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Sheet label={`Editar ${user.username}`} onClose={onClose}>
      <div className={styles.sheetTitle}>{user.username}</div>
      {user.must_change_pin && (
        <div className={styles.sheetSub}>Debe cambiar su PIN</div>
      )}
      {editableRoles && onRoleChange && (
        <>
          <label
            htmlFor="sheetRole"
            className={styles.roleLabel}
          >
            Rol
          </label>
          <select
            id="sheetRole"
            className={`${formStyles.addInput} ${styles.roleSelect}`}
            value={pendingRole || user.role}
            onChange={(e) => {
              setPendingRole(e.target.value);
              setRoleError('');
            }}
            disabled={busy}
            aria-label="Rol del usuario"
          >
            {editableRoles.map((r) => (
              <option key={r} value={r}>
                {getRoleLabel(r)}
              </option>
            ))}
          </select>
          {roleDirty && (
            <button
              type="button"
              className={styles.sheetAction}
              onClick={handleSaveRole}
              disabled={busy}
            >
              Guardar cambios
            </button>
          )}
          {roleError && (
            <div className={formStyles.errorBanner}>{roleError}</div>
          )}
        </>
      )}
      <HoldButton
        holdTime={800}
        size="md"
        disabled={busy}
        ariaLabel="Reiniciar PIN"
        doneLabel="PIN reiniciado"
        onHold={() => void handleReset()}
      >
        Reiniciar PIN
      </HoldButton>
      <div className={styles.sheetHint}>
        Genera un PIN temporal; al entrar deberá elegir uno nuevo.
      </div>
      {onDeleteUser && (
        <>
          <HoldButton
            holdTime={2000}
            size="md"
            disabled={busy}
            ariaLabel="Eliminar cuenta"
            backgroundColor="var(--bad-bg, #FFE9E7)"
            fillColor="var(--bad, #B3261E)"
            textColor="var(--bad-ink, #5F1710)"
            fillTextColor="#ffffff"
            doneLabel="Eliminada"
            onHold={() => void handleDelete()}
          >
            Eliminar cuenta
          </HoldButton>
          <div className={styles.sheetHint}>
            Se revocan sus sesiones y se liberan sus clickers.
          </div>
        </>
      )}
    </Sheet>
  );
};
