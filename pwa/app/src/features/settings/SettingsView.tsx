import React, { useState } from 'react';
import { ArrowLeft, Receipt, User as UserIcon, Users, Volume2, type LucideIcon } from 'lucide-react';
import { AccordionRow } from '../../shared/ui/Accordion/Accordion';
import { AccountCard } from '../auth/AccountCard';
import { User } from '../auth/auth.types';
import { RosterTable, type RosterTableProps } from '../roster/RosterTable';
import { RosterStudent } from '../roster/roster.types';
import { VoicePicker } from '../speech/VoicePicker';
import { AuditView } from '../staff/AuditView';
import styles from './settings.module.css';

/**
 * Roster data forwarded to the users section. Reuses the roster table's own
 * props (minus the student list, which arrives as `users`, and the editable
 * roles, which mirror the creatable roles) so the two can never drift apart.
 */
export interface SettingsRosterBundle
  extends Omit<RosterTableProps, 'students' | 'editableRoles'> {
  users: RosterStudent[];
}

export interface SettingsViewProps {
  user: User;
  onProfileChanged: () => Promise<unknown>;
  onSessionInvalidated: () => Promise<unknown> | void;
  onClose: () => void;
  roster?: SettingsRosterBundle;
  /** Gates the Voz / Auditoría sections (both need staff backends). */
  staffEnabled?: boolean;
}

type SectionId = 'cuenta' | 'usuarios' | 'voz' | 'auditoria';

/**
 * Teacher Settings list (FB Settings style accordion).
 * Sections mount incrementally: Cuenta first; Usuarios / Preguntas /
 * Actividad / Voz / Auditoría follow in later steps.
 */
export const SettingsView: React.FC<SettingsViewProps> = ({
  user,
  onProfileChanged,
  onSessionInvalidated,
  onClose,
  roster,
  staffEnabled = false,
}) => {
  const [open, setOpen] = useState<SectionId | null>(null);

  const toggle = (id: SectionId) =>
    setOpen((prev) => (prev === id ? null : id));

  const row = (
    id: SectionId,
    icon: LucideIcon,
    label: string,
    content: React.ReactNode,
    title?: string
  ) => (
    <AccordionRow
      key={id}
      id={id}
      icon={icon}
      label={label}
      content={content}
      title={title}
      open={open === id}
      onToggle={toggle}
    />
  );

  return (
    <div className={styles.list} id="s-settings">
      <button type="button" className={styles.backBtn} onClick={onClose}>
        <ArrowLeft size={18} aria-hidden /> Volver
      </button>

      {row(
        'cuenta',
        UserIcon,
        'Mi cuenta',
        <AccountCard
          user={user}
          onProfileChanged={onProfileChanged}
          onSessionInvalidated={onSessionInvalidated}
        />
      )}

      {roster &&
        row(
          'usuarios',
          Users,
          'Usuarios',
          <RosterTable
            students={roster.users}
            error={roster.error}
            pinNotice={roster.pinNotice}
            onAddStudent={roster.onAddStudent}
            onResetPin={roster.onResetPin}
            creatableRoles={roster.creatableRoles}
            deleted={roster.deleted}
            showDeleted={roster.showDeleted}
            onDeleteUser={roster.onDeleteUser}
            onRecoverUser={roster.onRecoverUser}
            onToggleDeleted={roster.onToggleDeleted}
            editableRoles={roster.creatableRoles}
            onRoleChange={roster.onRoleChange}
          />
        )}

      {staffEnabled &&
        row(
          'voz',
          Volume2,
          'Voz',
          <VoicePicker isAdmin={user.role === 'admin'} />
        )}

      {staffEnabled &&
        user.role === 'admin' &&
        row('auditoria', Receipt, 'Auditoría', <AuditView />, 'Solo admins')}
    </div>
  );
};
