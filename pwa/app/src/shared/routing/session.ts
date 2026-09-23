import { useEffect, useState } from 'react';
import type { UserRole } from '../../features/auth/auth.types';

/**
 * Canonical portal routing helpers. Replaces substring `includes('/maestro')`
 * checks, the 3x `?s=` parses and the host-address copies.
 */

export type Portal = 'student' | 'teacher' | 'display';

/** Exact first-segment portal match (no substring false-positives). */
export function getPortal(pathname: string): Portal {
  const segment = pathname.split('/').filter(Boolean)[0];
  if (segment === 'maestro') return 'teacher';
  if (segment === 'pantalla') return 'display';
  return 'student';
}

/** Extracts an optional pinned session UUID from `?s=<uuid>`. */
export function getSessionQueryParamId(search?: string): string | null {
  if (typeof window === 'undefined') return null;
  const raw = search ?? window.location.search;
  return new URLSearchParams(raw).get('s');
}

/** Post-login landing path, or null when already on the right portal. */
export function resolvePostLoginRedirect(
  role: UserRole | string | undefined,
  currentPath: string,
): string | null {
  const isStaff = role === 'teacher' || role === 'admin';
  if (isStaff) {
    return getPortal(currentPath) === 'teacher' ? null : '/maestro/';
  }
  return getPortal(currentPath) === 'teacher' ? '/alumno/' : null;
}

/** Current origin host for QR / join-address cards. SSR-safe. */
export function getHostAddress(): string {
  if (typeof window === 'undefined') return '';
  return window.location.host;
}

/** Reactive host address (updates once on mount for SSR parity). */
export function useHostAddress(): string {
  const [host, setHost] = useState(() => getHostAddress());
  useEffect(() => {
    setHost(getHostAddress());
  }, []);
  return host;
}
