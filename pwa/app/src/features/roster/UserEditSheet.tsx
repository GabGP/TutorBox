import React, { useEffect, useState } from 'react';
import { getRoleLabel } from '../../shared/constants/roles';
import { toErrorMessage } from '../../shared/lib/errors';
import formStyles from '../../shared/styles/forms.module.css';
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
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [busy, setBusy] = useState(false);
  const [roleError, setRoleError] = useState('');
  const [pendingRole, setPendingRole] = useState('');

  useEffect(() => {
    setConfirmDelete(false);
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
    if (!confirmDelete) {
      setConfirmDelete(true);
      return;
    }
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
            style={{ fontSize: '14px', fontWeight: 600, color: 'var(--mute2)' }}
          >
            Rol
          </label>
          <select
            id="sheetRole"
            className={formStyles.addInput}
            style={{ width: '100%' }}
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
      <button
        type="button"
        className={styles.sheetAction}
        onClick={handleReset}
        disabled={busy}
      >
        Reiniciar PIN
      </button>
      <div className={styles.sheetHint}>
        Genera un PIN temporal; al entrar deberá elegir uno nuevo.
      </div>
      {onDeleteUser && (
        <>
          <button
            type="button"
            className={`${styles.sheetAction} ${styles.sheetDanger}`}
            onClick={handleDelete}
            disabled={busy}
          >
            {confirmDelete ? 'Toca de nuevo para eliminar' : 'Eliminar cuenta'}
          </button>
          {confirmDelete && (
            <div className={styles.sheetHint}>
              Se revocan sus sesiones y se liberan sus clickers.
            </div>
          )}
        </>
      )}
    </Sheet>
  );
};
