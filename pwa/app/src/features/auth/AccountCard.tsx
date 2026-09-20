import React, { useState } from 'react';
import { authApi } from './authApi';
import { User } from './auth.types';
import styles from './auth.module.css';

export interface AccountCardProps {
  user: User;
  /** Refresh the parent user record (PIN change keeps the session alive). */
  onProfileChanged: () => Promise<unknown>;
  /** Username change revokes the session server-side; parent must log out. */
  onSessionInvalidated: () => Promise<unknown> | void;
}

/**
 * Self-service account maintenance card (FB/IG profile style).
 * Reuses the entry-form card language: avatar row, stacked inputs,
 * inline error/success banners. Wraps the previously unused
 * `PATCH /users/me/username` plus voluntary `PATCH /users/me/pin`.
 */
export const AccountCard: React.FC<AccountCardProps> = ({
  user,
  onProfileChanged,
  onSessionInvalidated,
}) => {
  const [namePin, setNamePin] = useState('');
  const [newUsername, setNewUsername] = useState('');
  const [pinCurrent, setPinCurrent] = useState('');
  const [newPin, setNewPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [nameError, setNameError] = useState('');
  const [pinError, setPinError] = useState('');
  const [notice, setNotice] = useState('');
  const [confirmName, setConfirmName] = useState(false);
  const [submitting, setSubmitting] = useState<'username' | 'pin' | null>(null);

  const handleUsernameChange = async () => {
    if (submitting) return;
    const cleanPin = namePin.trim();
    const cleanName = newUsername.trim();
    if (!cleanPin || !cleanName) {
      setNameError('Escribe tu PIN actual y el nombre nuevo');
      return;
    }
    // Renaming edits YOUR OWN account and ends the session: arm a
    // two-tap confirm so it never happens by accident.
    if (!confirmName) {
      setConfirmName(true);
      return;
    }
    setConfirmName(false);
    setSubmitting('username');
    setNameError('');
    setNotice('');
    try {
      // Server verifies the current PIN first (anti-oracle ordering).
      await authApi.changeUsername(cleanPin, cleanName);
      setNewUsername('');
      setNamePin('');
      setNotice('Nombre actualizado. Inicia sesión de nuevo.');
      await onSessionInvalidated();
    } catch (err: unknown) {
      const e = err as { status?: number; message?: string };
      setNameError(e.message || 'Error al cambiar el nombre');
    } finally {
      setSubmitting(null);
    }
  };
  const handlePinChange = async () => {
    if (submitting) return;
    const cleanCurrent = pinCurrent.trim();
    const a = newPin.trim();
    const b = confirmPin.trim();
    if (!cleanCurrent || !a || !b) {
      setPinError('Escribe tu PIN actual y el nuevo dos veces');
      return;
    }
    if (a !== b) {
      setPinError('Los dos PIN no coinciden');
      return;
    }
    if (a === cleanCurrent) {
      setPinError('El PIN nuevo debe ser diferente al actual');
      return;
    }
    setSubmitting('pin');
    setPinError('');
    setNotice('');
    try {
      // Server verifies the current PIN first; changePin re-authenticates,
      // so the session survives.
      await authApi.changePin(user.username, cleanCurrent, a);
      setPinCurrent('');
      setNewPin('');
      setConfirmPin('');
      setNotice('PIN actualizado.');
      await onProfileChanged();
    } catch (err: unknown) {
      const e = err as { status?: number; message?: string };
      setPinError(e.message || 'Error al cambiar el PIN');
    } finally {
      setSubmitting(null);
    }
  };

  const busyName = submitting === 'username';
  const busyPin = submitting === 'pin';

  return (
    <section className={styles.authCard} id="s-account">
      <div className={styles.profileRow}>
        <div className={styles.avatar} aria-hidden>
          {(user.username.charAt(0) || '?').toUpperCase()}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className={styles.profileName}>{user.username}</div>
          <div className={styles.profileRole}>
            {user.role === 'student'
              ? 'Alumno'
              : user.role === 'teacher'
                ? 'Docente'
                : 'Admin'}
          </div>
        </div>
      </div>

      {user.must_change_pin ? (
        <div className={styles.errorBanner}>
          Tienes un PIN temporal pendiente. Cámbialo primero con tu maestro.
        </div>
      ) : (
        <>
          <div className={styles.sectionLabel}>Tu nombre de usuario</div>
          <div className={styles.hint}>
            Cambia el nombre de TU cuenta (no crea una cuenta nueva) y
            deberás iniciar sesión de nuevo. Para crear una cuenta para
            otra persona usa Usuarios → Usuario nuevo.
          </div>
          <input
            id="accNamePin"
            type="password"
            inputMode="numeric"
            maxLength={8}
            autoComplete="current-password"
            placeholder="PIN actual (para cambiar nombre)"
            className={styles.inputField}
            value={namePin}
            onChange={(e) => {
              setNamePin(e.target.value);
              setConfirmName(false);
            }}
            disabled={busyName || busyPin}
          />
          <input
            id="accNewUser"
            className={styles.inputField}
            maxLength={32}
            autoComplete="username"
            placeholder="Nombre nuevo"
            value={newUsername}
            onChange={(e) => {
              setNewUsername(e.target.value);
              setConfirmName(false);
            }}
            disabled={busyName || busyPin}
          />
          <button
            type="button"
            id="accChangeUser"
            className={styles.submitBtn}
            onClick={handleUsernameChange}
            disabled={busyName || busyPin}
          >
            {confirmName ? 'Toca de nuevo para confirmar' : 'Cambiar mi nombre'}
          </button>
          {nameError && (
            <div className={styles.errorBanner} id="accNameErr">
              {nameError}
            </div>
          )}

          <input
            id="accPinCurrent"
            type="password"
            inputMode="numeric"
            maxLength={8}
            autoComplete="current-password"
            placeholder="PIN actual (para cambiar PIN)"
            className={styles.inputField}
            value={pinCurrent}
            onChange={(e) => setPinCurrent(e.target.value)}
            disabled={busyName || busyPin}
          />
          <input
            id="accNewPin"
            type="password"
            inputMode="numeric"
            maxLength={8}
            autoComplete="new-password"
            placeholder="PIN nuevo (4 a 8 números)"
            className={styles.inputField}
            value={newPin}
            onChange={(e) => setNewPin(e.target.value)}
            disabled={busyName || busyPin}
          />
          <input
            id="accNewPin2"
            type="password"
            inputMode="numeric"
            maxLength={8}
            autoComplete="new-password"
            placeholder="Repite el PIN nuevo"
            className={styles.inputField}
            value={confirmPin}
            onChange={(e) => setConfirmPin(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handlePinChange();
            }}
            disabled={busyName || busyPin}
          />
          <button
            type="button"
            id="accChangePin"
            className={styles.submitBtn}
            onClick={handlePinChange}
            disabled={busyName || busyPin}
          >
            Cambiar PIN
          </button>
          {pinError && (
            <div className={styles.errorBanner} id="accPinErr">
              {pinError}
            </div>
          )}
        </>
      )}

      {notice && (
        <div className={styles.successBanner} id="accNote">
          {notice}
        </div>
      )}
    </section>
  );
};
