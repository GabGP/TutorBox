import React, { useState } from 'react';
import { getRoleLabel } from '../../shared/constants/roles';
import formStyles from '../../shared/styles/forms.module.css';

export interface RosterAddFormProps {
  onAddStudent: (username: string, pin: string, role?: string) => Promise<unknown>;
  /** Roles the caller may create (e.g. ['student','teacher'] or + 'admin'). */
  creatableRoles?: string[];
}

/**
 * Inline user-addition form (username + PIN + optional role picker).
 * Mutation errors surface through the parent hook's banner, not here.
 */
export const RosterAddForm: React.FC<RosterAddFormProps> = ({
  onAddStudent,
  creatableRoles = ['student'],
}) => {
  const [username, setUsername] = useState('');
  const [pin, setPin] = useState('');
  const [role, setRole] = useState('student');
  const [submitting, setSubmitting] = useState(false);

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

  return (
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
  );
};
