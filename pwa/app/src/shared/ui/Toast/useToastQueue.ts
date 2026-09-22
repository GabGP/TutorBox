import { useCallback, useState } from 'react';
import type { ToastExitReason, ToastItem, ToastPush } from './toast.types';

let toastSeq = 0;

const nextToastId = (): string => {
  toastSeq += 1;
  return `toast-${Date.now().toString(36)}-${toastSeq}`;
};

export interface ToastQueue {
  toasts: ToastItem[];
  pushToast: (toast: ToastPush) => string;
  dismissToast: (id: string, _reason?: ToastExitReason) => void;
  clearToasts: () => void;
}

/**
 * In-memory toast queue (no timers here; ToastItem owns its fuse so
 * fake-timer tests stay deterministic). Cap keeps Jetson RAM bounded.
 */
export function useToastQueue(limit = 3): ToastQueue {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const pushToast = useCallback(
    (toast: ToastPush): string => {
      const id = toast.id ?? nextToastId();
      const item: ToastItem = {
        duration: 4000,
        tone: 'success',
        ...toast,
        id,
      };
      setToasts((prev) => [...prev.slice(-(limit - 1)), item]);
      return id;
    },
    [limit]
  );

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const clearToasts = useCallback(() => {
    setToasts([]);
  }, []);

  return { toasts, pushToast, dismissToast, clearToasts };
}
