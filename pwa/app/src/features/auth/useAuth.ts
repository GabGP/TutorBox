import { useCallback, useEffect, useRef, useState } from 'react';
import { User } from './auth.types';
import { authApi } from './authApi';

/**
 * Custom React hook for managing user authentication state, session restoration,
 * login/signup flows, forced PIN changes, and logout operations.
 *
 * @returns {object} Authentication state (`user`, `loading`, `mustChangePin`) and auth action handlers.
 */
export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [mustChangePin, setMustChangePin] = useState(false);
  const [pendingCredentials, setPendingCredentials] = useState<{
    username: string;
    currentPin: string;
  } | null>(null);
  const logoutInProgressRef = useRef(false);

  const restoreSession = useCallback(async () => {
    setLoading(true);
    try {
      const currentUser = await authApi.getCurrentUser();
      setUser(currentUser);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    restoreSession();
  }, [restoreSession]);

  const login = useCallback(async (username: string, pin: string) => {
    const res = await authApi.login(username, pin);
    if (res.must_change_pin) {
      setPendingCredentials({ username, currentPin: pin });
      setMustChangePin(true);
      return { mustChangePin: true };
    }
    const currentUser = await authApi.getCurrentUser();
    setUser(currentUser);
    return { mustChangePin: false, user: currentUser };
  }, []);

  const signupAndLogin = useCallback(
    async (username: string, pin: string) => {
      await authApi.signup(username, pin);
      return login(username, pin);
    },
    [login]
  );

  const handlePinChange = useCallback(
    async (newPin: string) => {
      if (!pendingCredentials) {
        throw new Error('No hay credenciales pendientes para cambio de PIN');
      }
      await authApi.changePin(
        pendingCredentials.username,
        pendingCredentials.currentPin,
        newPin
      );
      setMustChangePin(false);
      setPendingCredentials(null);
      const currentUser = await authApi.getCurrentUser();
      setUser(currentUser);
      return currentUser;
    },
    [pendingCredentials]
  );

  const logout = useCallback(async () => {
    if (logoutInProgressRef.current) return;
    logoutInProgressRef.current = true;
    try {
      await authApi.logout();
    } catch {
      // Quietly swallow if session was already invalidated
    } finally {
      setUser(null);
      setMustChangePin(false);
      setPendingCredentials(null);
      logoutInProgressRef.current = false;
    }
  }, []);

  return {
    user,
    loading,
    mustChangePin,
    pendingPin: pendingCredentials?.currentPin || null,
    login,
    signupAndLogin,
    handlePinChange,
    logout,
    restoreSession,
  };
}
