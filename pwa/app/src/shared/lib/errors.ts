import { getErrorMessage } from '../api/errorCatalog';

/**
 * Extracts a user-friendly message from any thrown value.
 * Single replacement for the 15+ `(err as {message}).message || 'Error...'` copies.
 */
export function toErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof Error && err.message) return err.message;
  if (typeof err === 'object' && err !== null && 'message' in err) {
    const message = (err as { message?: unknown }).message;
    if (typeof message === 'string' && message) return message;
  }
  if (typeof err === 'string' && err) return err;
  return fallback;
}

/** Maps roster API status codes to Spanish UX copy. */
export function mapRosterError(status: number | undefined, fallback: string): string {
  if (status === 409 || status === 403) {
    return getErrorMessage(status);
  }
  return fallback;
}
