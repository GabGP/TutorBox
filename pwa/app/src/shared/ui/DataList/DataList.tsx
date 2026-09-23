import React from 'react';
import styles from './DataList.module.css';

export interface DataListProps {
  /** Optional header row (column labels / counts). */
  header?: React.ReactNode;
  /** Shown when there are no children. */
  emptyText?: string;
  isEmpty?: boolean;
  /** True while a reload is in flight (exposed as aria-busy). */
  busy?: boolean;
  children: React.ReactNode;
  id?: string;
  ariaLabel?: string;
}

/**
 * Generic shadcn data-table-flavored list shell (list semantics, no
 * `<table>` fork). Header mimics the muted table head; rows are separated
 * by hairlines with a hover tint. Pair with `SwipeRow` rows and
 * `Pagination` below.
 */
export const DataList: React.FC<DataListProps> = ({
  header,
  emptyText = 'Sin resultados.',
  isEmpty = false,
  busy = false,
  children,
  id,
  ariaLabel,
}) => (
  <div
    className={styles.list}
    id={id}
    role="list"
    aria-label={ariaLabel}
    aria-busy={busy || undefined}
  >
    {header && <div className={styles.head}>{header}</div>}
    {isEmpty ? <div className={styles.empty}>{emptyText}</div> : children}
  </div>
);
