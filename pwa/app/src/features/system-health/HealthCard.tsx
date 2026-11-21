import React from 'react';
import { ProgressBar } from '../../shared/ui/ProgressBar/ProgressBar';
import type { HealthStatus } from './systemHealth.types';
import { STATUS_WORD } from './systemHealthFormat';
import styles from './systemHealth.module.css';

export interface HealthCardProps {
  title: string;
  /** Omitted for readings that have no limit (power, models, voices). */
  status?: HealthStatus;
  value: string;
  /** Percent drawn as a bar; omitted when there is no percent to show. */
  barPercent?: number | null;
  barLabel?: string;
  explanation: string;
  children?: React.ReactNode;
}

/**
 * One reading on the health panel: its title and status word, the value, an optional bar,
 * optional detail rows, and the short Spanish explanation of what it means.
 */
export const HealthCard: React.FC<HealthCardProps> = ({
  title,
  status,
  value,
  barPercent,
  barLabel,
  explanation,
  children,
}) => (
  <section className={styles.card} aria-label={title} data-status={status ?? 'none'}>
    <header className={styles.cardHead}>
      <h3 className={styles.cardTitle}>{title}</h3>
      {status && (
        <span className={`${styles.badge} ${styles[status]}`}>{STATUS_WORD[status]}</span>
      )}
    </header>
    <div className={styles.cardValue}>{value}</div>
    {barPercent !== undefined && barPercent !== null && (
      // The status class sets the bar's fill colour (the shared bar paints with --p).
      <div className={status ? styles[status] : undefined}>
        <ProgressBar value={barPercent} size="sm" animated={false} label={barLabel ?? title} />
      </div>
    )}
    {children}
    <p className={styles.explanation}>{explanation}</p>
  </section>
);
