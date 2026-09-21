import React, { useState } from 'react';
import { getRoleLabel } from '../../shared/constants/roles';
import formStyles from '../../shared/styles/forms.module.css';
import listStyles from '../../shared/styles/lists.module.css';
import styles from './roster.module.css';
import type { DeletedUser } from './roster.types';

export interface DeletedUsersViewProps {
  deleted?: DeletedUser[];
  showDeleted?: boolean;
  onToggleDeleted?: () => void;
  onRecoverUser?: (id: string, username: string) => Promise<unknown>;
}

/**
 * Soft-deleted accounts view with per-row recovery rename forms.
 * Hidden entirely when the parent offers no toggle.
 */
export const DeletedUsersView: React.FC<DeletedUsersViewProps> = ({
  deleted = [],
  showDeleted = false,
  onToggleDeleted,
  onRecoverUser,
}) => {
  const [recoverName, setRecoverName] = useState<Record<string, string>>({});

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
    <>
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
    </>
  );
};
