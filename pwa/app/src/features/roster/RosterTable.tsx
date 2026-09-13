import React, { useState } from 'react';
import styles from './roster.module.css';
import { RosterStudent } from './roster.types';

export interface RosterTableProps {
  students: RosterStudent[];
  error?: string | null;
  pinNotice?: string | null;
  onAddStudent: (username: string, pin: string) => Promise<unknown>;
  onResetPin: (id: string, username: string) => Promise<unknown>;
}

/**
 * Classroom Student Roster Management Table.
 * Renders the roster count, inline student addition form, error/notice banners,
 * and individual student PIN reset action buttons.
 *
 * @param {RosterTableProps} props - Component props containing students list, error/notice messages, and mutation handlers.
 * @returns {JSX.Element} The rendered student roster management interface.
 */
export const RosterTable: React.FC<RosterTableProps> = ({
  students,
  error,
  pinNotice,
  onAddStudent,
  onResetPin,
}) => {
  const [username, setUsername] = useState('');
  const [pin, setPin] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleAdd = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!username.trim() || !pin.trim()) return;

    setSubmitting(true);
    try {
      await onAddStudent(username.trim(), pin.trim());
      setUsername('');
      setPin('');
    } catch {
      // Error handled by parent hook
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.rowb}>
        <b>Alumnos registrados</b>
        <span id="rosterCount">{students.length}</span>
      </div>

      <div className={styles.addForm}>
        <input
          id="newUser"
          className={styles.addInput}
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
          className={styles.addInput}
          style={{ flex: '0 0 96px' }}
          inputMode="numeric"
          maxLength={8}
          placeholder="PIN"
          value={pin}
          onChange={(e) => setPin(e.target.value)}
          disabled={submitting}
        />
        <button
          type="button"
          id="addStudent"
          className={styles.submitAdd}
          onClick={handleAdd}
          disabled={submitting}
        >
          Agregar
        </button>
      </div>

      {error && (
        <div className={styles.errorBanner} id="rosterErr">
          {error}
        </div>
      )}

      {pinNotice && (
        <div className={styles.alert} id="pinNote">
          {pinNotice}
        </div>
      )}

      <div className={styles.rosterList} id="roster">
        {students.length === 0 ? (
          <div style={{ color: 'var(--mute)' }}>
            Todavía no hay alumnos. Agregue uno o pídales crear su cuenta en la dirección de arriba.
          </div>
        ) : (
          students.map((u) => (
            <div key={u.id} className={styles.rosterItem}>
              <span className={styles.studentName}>{u.username}</span>
              <button
                type="button"
                className={styles.resetBtn}
                data-id={u.id}
                data-name={u.username}
                onClick={() => onResetPin(u.id, u.username)}
              >
                Reiniciar PIN
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
