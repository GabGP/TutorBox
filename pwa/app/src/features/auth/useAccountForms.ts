import { useState } from 'react';
import { toErrorMessage } from '../../shared/lib/errors';
import { useToastQueue } from '../../shared/ui/Toast/useToastQueue';
import { authApi } from './authApi';
import type { User } from './auth.types';
import { validatePinPair } from './pinValidation';

export interface UsernameFormModel {
  namePin: string;
  newUsername: string;
  nameError: string;
  confirmName: boolean;
  busy: boolean;
  setNamePin: (v: string) => void;
  setNewUsername: (v: string) => void;
  handleUsernameChange: () => Promise<void>;
}

export interface PinFormModel {
  pinCurrent: string;
  newPin: string;
  confirmPin: string;
  pinError: string;
  busy: boolean;
  setPinCurrent: (v: string) => void;
  setNewPin: (v: string) => void;
  setConfirmPin: (v: string) => void;
  handlePinChange: () => Promise<void>;
}

interface UseAccountFormsCallbacks {
  onProfileChanged: () => Promise<unknown>;
  onSessionInvalidated: () => Promise<unknown> | void;
}

/**
 * State machine behind AccountCard: username self-rename (two-tap confirm,
 * ends the session) plus voluntary PIN rotation (re-authenticates, session
 * survives). The rename notice stays inline (the session ends right after);
 * the PIN confirmation floats as a toast.
 */
export function useAccountForms(
  user: User,
  { onProfileChanged, onSessionInvalidated }: UseAccountFormsCallbacks
) {
  const [namePin, setNamePinState] = useState('');
  const [newUsername, setNewUsernameState] = useState('');
  const [pinCurrent, setPinCurrent] = useState('');
  const [newPin, setNewPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [nameError, setNameError] = useState('');
  const [pinError, setPinError] = useState('');
  const [notice, setNotice] = useState('');
  const [confirmName, setConfirmName] = useState(false);
  const [submitting, setSubmitting] = useState<'username' | 'pin' | null>(null);
  const { toasts, pushToast, dismissToast } = useToastQueue();

  // Typing a new value disarms an armed rename confirm.
  const setNamePin = (v: string) => {
    setNamePinState(v);
    setConfirmName(false);
  };
  const setNewUsername = (v: string) => {
    setNewUsernameState(v);
    setConfirmName(false);
  };

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
      setNewUsernameState('');
      setNamePinState('');
      setNotice('Nombre actualizado. Inicia sesión de nuevo.');
      await onSessionInvalidated();
    } catch (err: unknown) {
      setNameError(toErrorMessage(err, 'Error al cambiar el nombre'));
    } finally {
      setSubmitting(null);
    }
  };

  const handlePinChange = async () => {
    if (submitting) return;
    const cleanCurrent = pinCurrent.trim();
    const a = newPin.trim();
    const b = confirmPin.trim();
    const pairError = validatePinPair(a, b, cleanCurrent);
    if (!cleanCurrent || pairError === 'empty') {
      setPinError('Escribe tu PIN actual y el nuevo dos veces');
      return;
    }
    if (pairError === 'mismatch') {
      setPinError('Los dos PIN no coinciden');
      return;
    }
    if (pairError === 'same') {
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
      pushToast({ message: 'PIN actualizado.' });
      await onProfileChanged();
    } catch (err: unknown) {
      setPinError(toErrorMessage(err, 'Error al cambiar el PIN'));
    } finally {
      setSubmitting(null);
    }
  };

  const username: UsernameFormModel = {
    namePin,
    newUsername,
    nameError,
    confirmName,
    busy: submitting === 'username',
    setNamePin,
    setNewUsername,
    handleUsernameChange,
  };
  const pin: PinFormModel = {
    pinCurrent,
    newPin,
    confirmPin,
    pinError,
    busy: submitting === 'pin',
    setPinCurrent,
    setNewPin,
    setConfirmPin,
    handlePinChange,
  };
  return { notice, username, pin, toasts, dismissToast, busy: submitting !== null };
}
