import { useEffect } from 'react';
import type { ToastPush } from './toast.types';

/**
 * Floats `error` as an error toast each time it turns on or changes. A poll
 * that keeps failing with the same message stays one toast; after a good
 * answer clears it, the next failure toasts again.
 */
export function useErrorToast(
  error: string | null | undefined,
  pushToast: (toast: ToastPush) => string
): void {
  useEffect(() => {
    if (error) pushToast({ message: error, tone: 'error' });
  }, [error, pushToast]);
}
