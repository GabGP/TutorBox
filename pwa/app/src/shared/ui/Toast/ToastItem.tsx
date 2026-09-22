import React, { useEffect, useRef, useState } from 'react';
import { X } from 'lucide-react';
import type { ToastExitReason, ToastItem } from './toast.types';
import styles from './Toast.module.css';

export interface ToastItemProps {
  toast: ToastItem;
  /** Swipe distance in px before release dismisses (slow drag). */
  swipeDistance?: number;
  dismissible?: boolean;
  onExit: (id: string, reason: ToastExitReason) => void;
}

/**
 * Single floating toast: auto-dismiss fuse, swipe-away drag, Esc and
 * close button. Success uses role=status; errors use role=alert.
 */
export const ToastItemView: React.FC<ToastItemProps> = ({
  toast,
  swipeDistance = 40,
  dismissible = true,
  onExit,
}) => {
  const duration = toast.duration ?? 4000;
  const tone = toast.tone ?? 'success';
  const [offset, setOffset] = useState<{ x: number; y: number } | null>(null);
  const [dragging, setDragging] = useState(false);
  const dragStart = useRef<{ x: number; y: number; t: number } | null>(null);
  const dragLast = useRef<{ x: number; y: number; t: number } | null>(null);

  useEffect(() => {
    if (!dismissible || duration <= 0) return;
    const timer = window.setTimeout(() => onExit(toast.id, 'timeout'), duration);
    return () => window.clearTimeout(timer);
  }, [dismissible, duration, onExit, toast.id]);

  useEffect(() => {
    if (!dismissible) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onExit(toast.id, 'escape');
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [dismissible, onExit, toast.id]);

  const onPointerDown = (event: React.PointerEvent): void => {
    if (!dismissible) return;
    dragStart.current = { x: event.clientX, y: event.clientY, t: performance.now() };
    dragLast.current = { x: event.clientX, y: event.clientY, t: performance.now() };
    setDragging(true);
  };

  const onPointerMove = (event: React.PointerEvent): void => {
    if (!dismissible || !dragStart.current) return;
    const dx = event.clientX - dragStart.current.x;
    const dy = event.clientY - dragStart.current.y;
    if (offset === null && Math.abs(dx) < 8 && Math.abs(dy) < 8) return;
    dragLast.current = { x: event.clientX, y: event.clientY, t: performance.now() };
    setOffset({ x: dx, y: dy });
  };

  const endDrag = (event: React.PointerEvent): void => {
    if (!dismissible || !dragStart.current) {
      dragStart.current = null;
      setDragging(false);
      setOffset(null);
      return;
    }
    const start = dragStart.current;
    const last = dragLast.current ?? { x: event.clientX, y: event.clientY, t: performance.now() };
    const dx = event.clientX - start.x;
    const dy = event.clientY - start.y;
    const dt = Math.max(1, performance.now() - last.t);
    const velocity = Math.hypot(event.clientX - last.x, event.clientY - last.y) / dt;
    dragStart.current = null;
    dragLast.current = null;
    setDragging(false);
    const farEnough = Math.abs(dy) > swipeDistance || Math.abs(dx) > swipeDistance;
    if (farEnough || velocity > 0.6) {
      setOffset(null);
      onExit(toast.id, 'swipe');
    } else {
      setOffset(null);
    }
  };

  const role = tone === 'error' ? 'alert' : 'status';

  return (
    <div
      className={`${styles.toast} ${styles[tone]} ${dragging ? styles.dragging : ''}`}
      role={role}
      aria-live={tone === 'error' ? 'assertive' : 'polite'}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={endDrag}
      onPointerCancel={() => {
        dragStart.current = null;
        dragLast.current = null;
        setDragging(false);
        setOffset(null);
      }}
      style={offset ? { transform: `translate(${offset.x}px, ${offset.y}px)` } : undefined}
    >
      <span className={styles.message}>{toast.message}</span>
      {dismissible && (
        <button
          type="button"
          className={styles.close}
          aria-label="Descartar aviso"
          onClick={() => onExit(toast.id, 'close')}
        >
          <X size={16} aria-hidden />
        </button>
      )}
    </div>
  );
};
