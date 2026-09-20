import React, { useId, useState } from 'react';
import styles from './Collapsible.module.css';

export interface CollapsibleProps {
  /** Visible toggle label. */
  title: string;
  /** Always-mounted content (preserves inner state, like `<details>`). */
  children: React.ReactNode;
  id?: string;
  defaultOpen?: boolean;
}

/**
 * Animated disclosure section: a smooth grid-rows expand/collapse
 * around always-mounted content. Closed content is `visibility:hidden`
 * so its controls never receive focus while collapsed.
 */
export const Collapsible: React.FC<CollapsibleProps> = ({
  title,
  children,
  id,
  defaultOpen = false,
}) => {
  const [open, setOpen] = useState(defaultOpen);
  const autoId = useId();
  const bodyId = `${id || autoId}-body`;

  return (
    <div id={id}>
      <button
        type="button"
        className={styles.toggle}
        aria-expanded={open}
        aria-controls={bodyId}
        onClick={() => setOpen((o) => !o)}
      >
        <span
          className={`${styles.chev} ${open ? styles.chevOpen : ''}`}
          aria-hidden
        >
          ▾
        </span>
        {title}
      </button>
      <div
        className={`${styles.collapse} ${open ? styles.collapseOpen : ''}`}
      >
        <div
          className={styles.body}
          role="region"
          id={bodyId}
          aria-label={title}
        >
          <div className={styles.bodyInner}>{children}</div>
        </div>
      </div>
    </div>
  );
};
