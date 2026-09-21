import React, { useState } from 'react';
import { getRoleLabel } from '../../shared/constants/roles';
import formStyles from '../../shared/styles/forms.module.css';
import listStyles from '../../shared/styles/lists.module.css';
import styles from './roster.module.css';
import { DeletedUsersView } from './DeletedUsersView';
import { RosterAddForm } from './RosterAddForm';
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
 * Classroom user roster: count header, add form, banners, active rows with
 * a single Editar affordance opening the floating edit card, plus the
 * soft-deleted accounts view. Form state lives in RosterAddForm and
 * DeletedUsersView; this component only hosts the edit sheet.
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
  const [editing, setEditing] = useState<RosterStudent | null>(null);

  return (
    <div className={listStyles.container}>
      <div className={listStyles.rowb}>
        <b>Usuarios registrados</b>
        <span id="rosterCount">{students.length}</span>
      </div>

      <RosterAddForm onAddStudent={onAddStudent} creatableRoles={creatableRoles} />

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

      <DeletedUsersView
        deleted={deleted}
        showDeleted={showDeleted}
        onToggleDeleted={onToggleDeleted}
        onRecoverUser={onRecoverUser}
      />
    </div>
  );
};
