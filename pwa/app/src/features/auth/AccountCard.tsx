import React from 'react';
import { getRoleLabel } from '../../shared/constants/roles';
import utils from '../../shared/styles/utils.module.css';
import { ToastViewport } from '../../shared/ui/Toast/ToastViewport';
import { User } from './auth.types';
import styles from './auth.module.css';
import { PinForm } from './PinForm';
import { useAccountForms } from './useAccountForms';
import { UsernameForm } from './UsernameForm';

export interface AccountCardProps {
  user: User;
  /** Refresh the parent user record (PIN change keeps the session alive). */
  onProfileChanged: () => Promise<unknown>;
  /** Username change revokes the session server-side; parent must log out. */
  onSessionInvalidated: () => Promise<unknown> | void;
}

/**
 * Self-service account maintenance card (FB/IG profile style).
 * Composes the profile header with the username rename and PIN rotation
 * forms; all state lives in useAccountForms.
 */
export const AccountCard: React.FC<AccountCardProps> = ({
  user,
  onProfileChanged,
  onSessionInvalidated,
}) => {
  const { notice, username, pin, toasts, dismissToast } = useAccountForms(user, {
    onProfileChanged,
    onSessionInvalidated,
  });

  return (
    <section className={styles.authCard} id="s-account">
      <div className={styles.profileRow}>
        <div className={styles.avatar} aria-hidden>
          {(user.username.charAt(0) || '?').toUpperCase()}
        </div>
        <div className={utils.grow}>
          <div className={styles.profileName}>{user.username}</div>
          <div className={styles.profileRole}>
            {getRoleLabel(user.role)}
          </div>
        </div>
      </div>

      {user.must_change_pin ? (
        <div className={styles.errorBanner}>
          Tienes un PIN temporal pendiente. Cámbialo primero con tu maestro.
        </div>
      ) : (
        <>
          <UsernameForm form={username} disabled={pin.busy} />
          <PinForm form={pin} disabled={username.busy} />
        </>
      )}

      {notice && (
        <div className={styles.successBanner} id="accNote">
          {notice}
        </div>
      )}
      <ToastViewport toasts={toasts} onDismiss={(id) => dismissToast(id)} />
    </section>
  );
};
