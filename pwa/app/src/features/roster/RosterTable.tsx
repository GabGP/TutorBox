import React, { useState } from 'react';
import { getRoleLabel } from '../../shared/constants/roles';
import formStyles from '../../shared/styles/forms.module.css';
import listStyles from '../../shared/styles/lists.module.css';
import styles from './roster.module.css';
import { DeletedUser, RosterStudent } from './roster.types';
import { UserEditSheet } from './UserEditSheet';

export interface RosterTableProps {
  students: RosterStudent[];
  error?: string | null;
  pinNotice?: string | null;
  onAddStudent: (username: string, pin: string, role?: string) => Promise<unknown>;
  onResetPin: (id: string, username: string) => Promise<unknown>;
  /** Roles the caller may create (e.g. ['student','teacher'] or + 'admin'). */
  creatableRoles?: string[];
  deleted?: DeletedUser[];
  showDeleted?: boolean;
  onDeleteUser?: (id: string, username: string) => Promise<unknown>;
  onRecoverUser?: (id: string, username: string) => Promise<unknown>;
  onToggleDeleted?: () => void;
  /** Roles assignable in the edit sheet; hidden when absent (e.g. lobby). */
  editableRoles?: string[];
  onRoleChange?: (id: string, role: string) => Promise<unknown>;
}

/**
 * Classroom User Roster Management Table.
 * Renders the roster count, inline user addition form (with role picker),
 * error/notice banners, compact rows with a single Editar affordance that
 * opens the floating edit card, and an optional soft-deleted accounts view
 * with recovery.
 */
export const RosterTable: React.FC<RosterTableProps> = ({
  students,
  error,
  pinNotice,
  onAddStudent,
  onResetPin,
  creatableRoles = ['student'],
  deleted = [],
  showDeleted = false,
  onDeleteUser,
  onRecoverUser,
  onToggleDeleted,
  editableRoles,
  onRoleChange,
}) => {
  const [username, setUsername] = useState('');
  const [pin, setPin] = useState('');
  const [role, setRole] = useState('student');
  const [submitting, setSubmitting] = useState(false);
  const [editing, setEditing] = useState<RosterStudent | null>(null);
  const [recoverName, setRecoverName] = useState<Record<string, string>>({});

  const handleAdd = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!username.trim() || !pin.trim()) return;

    setSubmitting(true);
    try {
      await onAddStudent(username.trim(), pin.trim(), role);
      setUsername('');
      setPin('');
    } catch {
      // Error handled by parent hook
    } finally {
      setSubmitting(false);
    }
  };

  const handleRecover = async (id: string) => {
    const name = (recoverName[id] || '').trim();
    if (!name || !onRecoverUser) return;
    try {
      await onRecoverUser(id, name);
      setRecoverName((prev) => ({ ...prev, [id]: '' }));
    } catch {
      // Error handled by parent hook
    }
  };

  return (
    <div className={listStyles.container}>
      <div className={listStyles.rowb}>
        <b>Usuarios registrados</b>
        <span id="rosterCount">{students.length}</span>
      </div>

      <div className={formStyles.addForm}>
        <input
          id="newUser"
          className={formStyles.addInput}
          style={{ flex: 1 }}
          maxLength={32}
          placeholder="Usuario nuevo"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          disabled={submitting}
        />
        <input
          id="newPin"
          type="password"
          className={formStyles.addInput}
          style={{ flex: '0 0 96px' }}
          inputMode="numeric"
          maxLength={8}
          placeholder="PIN"
          value={pin}
          onChange={(e) => setPin(e.target.value)}
          disabled={submitting}
        />
        {creatableRoles.length > 1 && (
          <select
            id="newRole"
            className={formStyles.addInput}
            style={{ flex: '0 0 120px' }}
            value={role}
            onChange={(e) => setRole(e.target.value)}
            disabled={submitting}
            aria-label="Rol"
          >
            {creatableRoles.map((r) => (
              <option key={r} value={r}>
                {getRoleLabel(r)}
              </option>
            ))}
          </select>
        )}
        <button
          type="button"
          id="addStudent"
          className={formStyles.submitAdd}
          onClick={handleAdd}
          disabled={submitting}
        >
          Agregar
        </button>
      </div>

      {error && (
        <div className={formStyles.errorBanner} id="rosterErr">
          {error}
        </div>
      )}

      {pinNotice && (
        <div className={formStyles.alert} id="pinNote">
          {pinNotice}
        </div>
      )}

      <div className={listStyles.rosterList} id="roster">
        {students.length === 0 ? (
          <div style={{ color: 'var(--mute)' }}>
            Todavía no hay alumnos. Agregue uno o pídales crear su cuenta en la dirección de arriba.
          </div>
        ) : (
          students.map((u) => (
            <div key={u.id} className={listStyles.rosterItem}>
              <span className={listStyles.studentName}>{u.username}</span>
              <span className={listStyles.roleTag}>{getRoleLabel(u.role)}</span>
              <button
                type="button"
                className={styles.resetBtn}
                data-id={u.id}
                data-name={u.username}
                onClick={() => setEditing(u)}
              >
                Editar
              </button>
            </div>
          ))
        )}
      </div>

      <UserEditSheet
        user={editing}
        onClose={() => setEditing(null)}
        onResetPin={onResetPin}
        onDeleteUser={onDeleteUser}
        editableRoles={editableRoles}
        onRoleChange={onRoleChange}
      />

      {onToggleDeleted && (
        <button
          type="button"
          className={formStyles.toggleLink}
          onClick={onToggleDeleted}
        >
          {showDeleted ? 'Ocultar eliminados' : 'Ver eliminados'}
        </button>
      )}

      {showDeleted && (
        <div className={listStyles.rosterList} id="rosterDeleted">
          {deleted.length === 0 ? (
            <div style={{ color: 'var(--mute)' }}>No hay cuentas eliminadas.</div>
          ) : (
            deleted.map((u) => (
              <div key={u.id} className={listStyles.rosterItem}>
                <span className={listStyles.studentName}>{u.former_username}</span>
                <span className={listStyles.roleTag}>{getRoleLabel(u.role)}</span>
                {onRecoverUser && (
                  <span className={styles.recoverRow}>
                    <input
                      className={formStyles.addInput}
                      style={{ flex: 1, height: '40px', fontSize: '15px' }}
                      maxLength={32}
                      placeholder="Nombre nuevo"
                      value={recoverName[String(u.id)] || ''}
                      onChange={(e) =>
                        setRecoverName((prev) => ({
                          ...prev,
                          [String(u.id)]: e.target.value,
                        }))
                      }
                    />
                    <button
                      type="button"
                      className={styles.resetBtn}
                      onClick={() => handleRecover(String(u.id))}
                    >
                      Recuperar
                    </button>
                  </span>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};
