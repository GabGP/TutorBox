import React, { useEffect, useRef, useState } from 'react';
import { ChevronDown, type LucideIcon } from 'lucide-react';
import styles from './Accordion.module.css';

export interface AccordionRowProps<TId extends string> {
  id: TId;
  icon: LucideIcon;
  label: string;
  content: React.ReactNode;
  title?: string;
  open: boolean;
  onToggle: (id: TId) => void;
  /** Must match the .collapse grid-rows transition. */
  collapseMs?: number;
}

/**
 * Animated accordion row: content mounts instantly on open and stays mounted
 * through the collapse transition on close.
 */
export function AccordionRow<TId extends string>({
  id,
  icon,
  label,
  content,
  title,
  open,
  onToggle,
  collapseMs = 320,
}: AccordionRowProps<TId>) {
  const [rendered, setRendered] = useState(open);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (open) {
      if (timer.current) clearTimeout(timer.current);
      setRendered(true);
      return;
    }
    // Keep content for the collapse animation, then unmount.
    timer.current = setTimeout(() => setRendered(false), collapseMs);
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, [open, collapseMs]);

  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
    },
    []
  );

  const Icon = icon;
  return (
    <div className={styles.row}>
      <button
        type="button"
        className={styles.rowBtn}
        onClick={() => onToggle(id)}
        aria-expanded={open}
        title={title}
      >
        <span aria-hidden className={styles.rowIcon}><Icon size={18} aria-hidden /></span> {label}
        <span
          className={`${styles.chev} ${open ? styles.chevOpen : ''}`}
          aria-hidden
        >
          <ChevronDown size={18} aria-hidden />
        </span>
      </button>
      <div
        className={`${styles.collapse} ${open ? styles.collapseOpen : ''}`}
      >
        <div className={styles.body}>{rendered ? content : null}</div>
      </div>
    </div>
  );
}
