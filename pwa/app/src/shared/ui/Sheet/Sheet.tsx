import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import styles from './Sheet.module.css';

export interface SheetProps {
  /** Accessible dialog label. */
  label: string;
  onClose: () => void;
  children: React.ReactNode;
}

/**
 * Shared floating sheet (IG-style bottom sheet on phone, centered dialog
 * on desktop). Portaled to document.body so ancestor transforms (e.g.
 * accordion expand animations) never trap it. Drag the grip downward,
 * tap the backdrop, or press Esc to collapse.
 */
export const Sheet: React.FC<SheetProps> = ({ label, onClose, children }) => {
  const [dragDy, setDragDy] = useState(0);
  const [dragging, setDragging] = useState(false);
  const dragStartY = useRef(0);
  const dragLastY = useRef(0);
  const dragLastT = useRef(0);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  // Lock background scroll while open; backdrop taps still dismiss.
  // body-only `overflow` is ignored by touch momentum scrolling, so also
  // lock the root element and swallow backdrop touchmoves (non-passive).
  // Touches inside the sheet panel keep their native scroll.
  const overlayRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const prevBody = document.body.style.overflow;
    const prevHtml = document.documentElement.style.overflow;
    document.body.style.overflow = 'hidden';
    document.documentElement.style.overflow = 'hidden';
    const overlay = overlayRef.current;
    const onTouchMove = (e: TouchEvent) => {
      if (e.target === overlay) e.preventDefault();
    };
    overlay?.addEventListener('touchmove', onTouchMove, { passive: false });
    return () => {
      document.body.style.overflow = prevBody;
      document.documentElement.style.overflow = prevHtml;
      overlay?.removeEventListener('touchmove', onTouchMove);
    };
  }, []);

  const onGripDown = (e: React.PointerEvent) => {
    dragStartY.current = e.clientY;
    dragLastY.current = e.clientY;
    dragLastT.current = performance.now();
    setDragging(true);
    (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
  };

  const onGripMove = (e: React.PointerEvent) => {
    if (!dragging) return;
    const dy = Math.max(0, e.clientY - dragStartY.current);
    dragLastY.current = e.clientY;
    dragLastT.current = performance.now();
    setDragDy(dy);
  };

  const onGripUp = (e: React.PointerEvent) => {
    if (!dragging) return;
    setDragging(false);
    const dt = Math.max(1, performance.now() - dragLastT.current);
    const velocity = (e.clientY - dragLastY.current) / dt;
    // Collapse on a long pull or a fast downward flick.
    if (dragDy > 120 || velocity > 0.6) {
      setDragDy(0);
      onClose();
    } else {
      setDragDy(0);
    }
  };

  return createPortal(
    <div
      ref={overlayRef}
      className={styles.sheetOverlay}
      onClick={onClose}
      role="presentation"
    >
      <div
        className={`${styles.sheet} ${dragging ? styles.sheetDragging : ''}`}
        role="dialog"
        aria-label={label}
        onClick={(e) => e.stopPropagation()}
        style={dragDy > 0 ? { transform: `translateY(${dragDy}px)` } : undefined}
      >
        <div
          className={styles.sheetGrip}
          aria-hidden
          onPointerDown={onGripDown}
          onPointerMove={onGripMove}
          onPointerUp={onGripUp}
          onPointerCancel={() => {
            setDragging(false);
            setDragDy(0);
          }}
        >
          <div className={styles.sheetHandle} />
        </div>
        {children}
      </div>
    </div>,
    document.body
  );
};
