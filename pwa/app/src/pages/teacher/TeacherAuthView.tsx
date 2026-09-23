import React from 'react';
import { EntryForm } from '../../features/auth/EntryForm';
import { ForcedPinModal } from '../../features/auth/ForcedPinModal';
import { ServerBadge } from '../../shared/ui/ServerBadge/ServerBadge';
import styles from './TeacherView.module.css';

export interface TeacherAuthViewProps {
  mustChangePin: boolean;
  pendingPin?: string | null;
  roleError: string | null;
  onLogin: (username: string, pin: string) => Promise<unknown>;
  onPinChange: (newPin: string) => Promise<unknown>;
}

/**
 * Teacher Authentication and PIN Rotation Gateway Shell.
 * Renders the teacher login form or forced PIN modal before granting access to classroom controls.
 *
 * @param {TeacherAuthViewProps} props - Component props containing auth status and callback handlers.
 * @returns {JSX.Element} The rendered teacher authentication card.
 */
export const TeacherAuthView: React.FC<TeacherAuthViewProps> = ({
  mustChangePin,
  pendingPin,
  roleError,
  onLogin,
  onPinChange,
}) => {
  if (mustChangePin) {
    return (
      <main className={styles.mainContent}>
        <ForcedPinModal currentPin={pendingPin} onPinChange={onPinChange} />
      </main>
    );
  }

  return (
    <main className={styles.mainContent}>
      <EntryForm
        title="Panel del docente"
        subtitle="Entran docentes y admins. Alumnos: usen /alumno/."
        onLogin={onLogin}
        externalError={roleError}
        headerExtra={<ServerBadge />}
      />
    </main>
  );
};
