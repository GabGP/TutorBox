import React, { useCallback, useEffect, useRef, useState } from 'react';
import styles from './SwipeRow.module.css';

export interface SwipeRowAction {
  /** Stable key. */
  key: string;
  /** Visible label under/beside the icon. */
  label: string;
  /** Accessible name. Falls back to label. */
  ariaLabel?: string;
  /** Icon node (e.g. lucide icon). */
  icon?: React.ReactNode;
  /** Visual tone. */
  tone?: 'default' | 'danger';
  /** Fired on tap/click (and keyboard Enter/Space). */
  onActivate: () => void;
}

export interface SwipeRowProps {
  /** Row face content. */
  children: React.ReactNode;
  /** Trailing actions revealed by swiping left. */
  actions: SwipeRowAction[];
  /** Controlled open state. Uncontrolled when omitted. */
  open?: boolean;
  /** Fired when open state changes (drag, Esc, action tap). */
  onOpenChange?: (open: boolean) => void;
  disabled?: boolean;
  className?: string;
  /** Accessible label for the row face region. */
  ariaLabel?: string;
}

const OPEN_THRESHOLD_PX = 40;

/**
 * Generic swipe-to-reveal row: drag the face left (touch or mouse) to
 * expose trailing icon actions. Works the same with touch and mouse, so
 * it doubles as the desktop interaction (no hover-only affordances).
 * Actions are plain buttons so keyboard/screen-reader users never need
 * to swipe. Esc closes. Respects `prefers-reduced-motion`.
 */
export const SwipeRow: React.FC<SwipeRowProps> = ({
  children,
  actions,
  open: controlledOpen,
  onOpenChange,
  disabled = false,
  className = '',
  ariaLabel,
}) => {
  const [uncontrolledOpen, setUncontrolledOpen] = useState(false);
  const open = controlledOpen ?? uncontrolledOpen;
  const setOpen = useCallback(
    (next: boolean) => {
      if (controlledOpen === undefined) setUncontrolledOpen(next);
      onOpenChange?.(next);
    },
    [controlledOpen, onOpenChange]
  );

  const [dragX, setDragX] = useState<number | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const actionsRef = useRef<HTMLDivElement>(null);
  const dragState = useRef<{ startX: number; baseOpen: boolean } | null>(null);

  // Close on Escape for keyboard users.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, setOpen]);

  const actionsWidth = () => actionsRef.current?.offsetWidth ?? 0;

  const onPointerDown = (e: React.PointerEvent) => {
    if (disabled || actions.length === 0) return;
    // Only start a horizontal-drag tracking session; never preventDefault
    // so vertical scroll and button taps keep working.
    dragState.current = { startX: e.clientX, baseOpen: open };
  };

  const onPointerMove = (e: React.PointerEvent) => {
    const st = dragState.current;
    if (!st || disabled) return;
    const dx = e.clientX - st.startX;
    // Only engage once there is meaningful horizontal intent.
    if (dragX === null && Math.abs(dx) < 8) return;
    const base = st.baseOpen ? -actionsWidth() : 0;
    const next = Math.min(0, Math.max(base + dx, -actionsWidth()));
    setDragX(next);
  };

  const endDrag = (e: React.PointerEvent) => {
    const st = dragState.current;
    dragState.current = null;
    if (st === null || dragX === null) {
      setDragX(null);
      return;
    }
    const dx = e.clientX - st.startX;
    const width = Math.max(1, actionsWidth());
    if (!st.baseOpen && dx < -OPEN_THRESHOLD_PX) {
      setOpen(true);
    } else if (st.baseOpen && dx > OPEN_THRESHOLD_PX) {
      setOpen(false);
    } else {
      // Snap back; also open on a long flick past half the action strip.
      if (!st.baseOpen && Math.abs(dx) > width / 2) setOpen(true);
      else if (st.baseOpen && dx > -width / 2) setOpen(false);
      else setOpen(st.baseOpen);
    }
    setDragX(null);
  };

  const faceTransform =
    dragX !== null
      ? { transform: `translateX(${dragX}px)`, transition: 'none' }
      : open
        ? { transform: `translateX(${-actionsWidth()}px)` }
        : undefined;

  return (
    <div
      ref={rootRef}
      className={`${styles.swipe} ${open ? styles.isOpen : ''} ${className}`}
      data-open={open ? 'true' : 'false'}
    >
      <div ref={actionsRef} className={styles.actions}>
        {actions.map((a) => (
          <button
            key={a.key}
            type="button"
            className={`${styles.actionBtn} ${a.tone === 'danger' ? styles.danger : styles.plain}`}
            aria-label={a.ariaLabel ?? a.label}
            onFocus={() => {
              if (!disabled && actions.length > 0) setOpen(true);
            }}
            onClick={() => {
              a.onActivate();
              // Keep the strip open unless the parent drives it closed
              // (e.g. delete arms confirm, edit/info navigate away).
            }}
          >
            {a.icon && <span className={styles.actionIcon} aria-hidden>{a.icon}</span>}
            <span className={styles.actionLabel}>{a.label}</span>
          </button>
        ))}
      </div>
      <div
        className={styles.face}
        style={faceTransform}
        aria-label={ariaLabel}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={endDrag}
        onPointerCancel={() => {
          dragState.current = null;
          setDragX(null);
        }}
      >
        {children}
      </div>
    </div>
  );
};
