import React from 'react';
import { createPortal } from 'react-dom';
import { ToastItemView } from './ToastItem';
import type { ToastExitReason, ToastItem } from './toast.types';
import styles from './Toast.module.css';

export interface ToastViewportProps {
  toasts: ToastItem[];
  onDismiss: (id: string, reason: ToastExitReason) => void;
  swipeDistance?: number;
}

/**
 * Floating toast viewport (portaled to body so sheet transforms never
 * trap it). Bottom-center on phone, bottom-right on desktop, above
 * sheets. Layout never shifts: toasts overlay content.
 */
export const ToastViewport: React.FC<ToastViewportProps> = ({
  toasts,
  onDismiss,
  swipeDistance,
}) => {
  if (toasts.length === 0) return null;
  return createPortal(
    <div className={styles.viewport} aria-live="polite" data-testid="toast-viewport">
      {toasts.map((toast) => (
        <ToastItemView
          key={toast.id}
          toast={toast}
          swipeDistance={swipeDistance}
          onExit={onDismiss}
        />
      ))}
    </div>,
    document.body
  );
};
