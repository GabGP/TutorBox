import React, { useEffect, useState } from 'react';
import { toErrorMessage } from '../../shared/lib/errors';
import { ToastViewport } from '../../shared/ui/Toast/ToastViewport';
import { useToastQueue } from '../../shared/ui/Toast/useToastQueue';
import styles from './auth.module.css';

export { resolvePostLoginRedirect } from '../../shared/routing/session';

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
 * Unified entry form for all roles (student, teacher, admin).
 * Same card/inputs/buttons as before; `allowSignup` gates the student
 * self-registration mode (signup always creates `role=student` server-side).
 * Role elevation happens via staff roster creation, not here.
 * Failures float as error toasts so the card never shifts layout.
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
  const [submitting, setSubmitting] = useState(false);
  const { toasts, pushToast, dismissToast } = useToastQueue();

  const fail = (message: string) =>
    pushToast({ message, tone: 'error' });

  useEffect(() => {
    if (externalError) fail(externalError);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [externalError]);

  const toggleMode = () => {
    setMode((prev) => (prev === 'login' ? 'signup' : 'login'));
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (submitting) return;
    const cleanUser = username.trim();
    const cleanPin = pin.trim();

    if (!cleanUser || !cleanPin) {
      fail('Escribe tu usuario y tu PIN');
      return;
    }

    setSubmitting(true);

    try {
      if (mode === 'signup' && onSignup) {
        await onSignup(cleanUser, cleanPin);
      } else {
        await onLogin(cleanUser, cleanPin);
      }
    } catch (err: unknown) {
      const e = err as { status?: number };
      if (e.status === 409) {
        fail('Ese nombre ya está en uso, elige otro');
      } else {
        fail(toErrorMessage(err, 'Error al iniciar sesión'));
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

      <ToastViewport toasts={toasts} onDismiss={(id) => dismissToast(id)} />

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
