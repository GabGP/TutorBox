import React, { useEffect, useState } from 'react';
import { AccountCard } from '../auth/AccountCard';
import { User } from '../auth/auth.types';
import { RosterTable } from '../roster/RosterTable';
import { DeletedUser, RosterStudent } from '../roster/roster.types';
import { VoicePicker } from '../speech/VoicePicker';
import { AuditView } from '../staff/AuditView';
import styles from './settings.module.css';

export interface SettingsRosterBundle {
  users: RosterStudent[];
  error: string | null;
  pinNotice: string | null;
  onAddStudent: (username: string, pin: string, role?: string) => Promise<unknown>;
  onResetPin: (id: string, username: string) => Promise<unknown>;
  creatableRoles: string[];
  deleted: DeletedUser[];
  showDeleted: boolean;
  onDeleteUser: (id: string, username: string) => Promise<unknown>;
  onRecoverUser: (id: string, username: string) => Promise<unknown>;
  onToggleDeleted: () => void;
  onRoleChange: (id: string, role: string) => Promise<unknown>;
}

export interface SettingsViewProps {
  user: User;
  onProfileChanged: () => Promise<unknown>;
  onSessionInvalidated: () => Promise<unknown> | void;
  onClose: () => void;
  roster?: SettingsRosterBundle;
  bankEnabled?: boolean;
}

type SectionId = 'cuenta' | 'usuarios' | 'voz' | 'auditoria';

/** Matches the .collapse grid-rows transition in settings.module.css. */
const COLLAPSE_MS = 320;

interface SettingsRowProps {
  id: SectionId;
  icon: string;
  label: string;
  content: React.ReactNode;
  title?: string;
  open: boolean;
  onToggle: (id: SectionId) => void;
}

/**
 * Accordion row that animates both ways: content mounts instantly on open
 * and stays mounted through the collapse transition on close.
 */
const SettingsRow: React.FC<SettingsRowProps> = ({
  id,
  icon,
  label,
  content,
  title,
  open,
  onToggle,
}) => {
  const [rendered, setRendered] = useState(open);
  const timer = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (open) {
      if (timer.current) clearTimeout(timer.current);
      setRendered(true);
      return;
    }
    // Keep content for the collapse animation, then unmount.
    timer.current = setTimeout(() => setRendered(false), COLLAPSE_MS);
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, [open ]);

  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
    },
    []
  );

  return (
    <div className={styles.row}>
      <button
        type="button"
        className={styles.rowBtn}
        onClick={() => onToggle(id)}
        aria-expanded={open}
        title={title}
      >
        <span aria-hidden>{icon}</span> {label}
        <span
          className={`${styles.chev} ${open ? styles.chevOpen : ''}`}
          aria-hidden
        >
          ▾
        </span>
      </button>
      <div
        className={`${styles.collapse} ${open ? styles.collapseOpen : ''}`}
      >
        <div className={styles.body}>{rendered ? content : null}</div>
      </div>
    </div>
  );
};

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
  bankEnabled = false,
}) => {
  const [open, setOpen] = useState<SectionId | null>(null);

  const toggle = (id: SectionId) =>
    setOpen((prev) => (prev === id ? null : id));

  const row = (
    id: SectionId,
    icon: string,
    label: string,
    content: React.ReactNode,
    title?: string
  ) => (
    <SettingsRow
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
        ← Volver
      </button>

      {row(
        'cuenta',
        '👤',
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
          '👥',
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

      {bankEnabled &&
        row(
          'voz',
          '🔊',
          'Voz',
          <VoicePicker isAdmin={user.role === 'admin'} />
        )}

      {bankEnabled &&
        user.role === 'admin' &&
        row('auditoria', '🧾', 'Auditoría', <AuditView />, 'Solo admins')}
    </div>
  );
};
