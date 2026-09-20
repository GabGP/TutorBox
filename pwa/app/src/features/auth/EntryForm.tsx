import React, { useState } from 'react';
import { UserRole } from './auth.types';
import styles from './auth.module.css';

export interface EntryFormProps {
  title: string;
  subtitle?: string;
  allowSignup?: boolean;
  onLogin: (username: string, pin: string) => Promise<unknown>;
  onSignup?: (username: string, pin: string) => Promise<unknown>;
  headerExtra?: React.ReactNode;
  idPrefix?: string;
  externalError?: string | null;
}

/**
 * Resolves the post-login landing page for a role relative to the current portal.
 * Students belong on /alumno/, staff (teacher/admin) on /maestro/.
 * Returns the target path, or null when already on the right portal.
 */
export function resolvePostLoginRedirect(
  role: UserRole | string | undefined,
  currentPath: string
): string | null {
  const isStaff = role === 'teacher' || role === 'admin';
  if (isStaff) {
    return currentPath.includes('/maestro') ? null : '/maestro/';
  }
  return currentPath.includes('/maestro') ? '/alumno/' : null;
}

/**
 * Unified entry form for all roles (student, teacher, admin).
 * Same card/inputs/buttons as before; `allowSignup` gates the student
 * self-registration mode (signup always creates `role=student` server-side).
 * Role elevation happens via staff roster creation, not here.
 */
export const EntryForm: React.FC<EntryFormProps> = ({
  title,
  subtitle,
  allowSignup = false,
  onLogin,
  onSignup,
  headerExtra,
  externalError,
}) => {
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [username, setUsername] = useState('');
  const [pin, setPin] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const toggleMode = () => {
    setMode((prev) => (prev === 'login' ? 'signup' : 'login'));
    setError('');
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (submitting) return;
    const cleanUser = username.trim();
    const cleanPin = pin.trim();

    if (!cleanUser || !cleanPin) {
      setError('Escribe tu usuario y tu PIN');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      if (mode === 'signup' && onSignup) {
        await onSignup(cleanUser, cleanPin);
      } else {
        await onLogin(cleanUser, cleanPin);
      }
    } catch (err: unknown) {
      const e = err as { status?: number; message?: string };
      if (e.status === 409) {
        setError('Ese nombre ya está en uso, elige otro');
      } else {
        setError(e.message || 'Error al iniciar sesión');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className={styles.authCard} id="s-login">
      <div className={styles.logo}>T</div>
      <div className={styles.titleBlock}>
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>

      {headerExtra}

      <input
        id="user"
        className={styles.inputField}
        maxLength={32}
        autoComplete="username"
        placeholder="Tu usuario"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        disabled={submitting}
      />

      <input
        id="pin"
        type="password"
        inputMode="numeric"
        maxLength={8}
        autoComplete="current-password"
        placeholder="PIN"
        className={styles.inputField}
        value={pin}
        onChange={(e) => setPin(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') handleSubmit();
        }}
        disabled={submitting}
      />

      {(error || externalError) && (
        <div className={styles.errorBanner} id="lerr">
          {error || externalError}
        </div>
      )}

      <button
        type="button"
        id="enter"
        className={styles.submitBtn}
        onClick={() => handleSubmit()}
        disabled={submitting}
      >
        {mode === 'login' ? 'Entrar' : 'Crear cuenta y entrar'}
      </button>

      {allowSignup && (
        <button
          type="button"
          id="signup"
          className={styles.toggleLink}
          onClick={toggleMode}
          disabled={submitting}
        >
          {mode === 'login' ? '¿Primera vez? Crear cuenta' : 'Ya tengo cuenta'}
        </button>
      )}
    </section>
  );
};
