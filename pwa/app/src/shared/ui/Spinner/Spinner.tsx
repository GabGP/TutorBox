import React from 'react';
import styles from './Spinner.module.css';

export interface SpinnerProps {
  /** What is loading, announced once by screen readers (e.g. "Cargando el modelo del tutor…"). */
  label: string;
  /** Diameter in pixels. */
  size?: number;
  className?: string;
}

/**
 * Small loading ring for a request that is still pending. It is a status region named by
 * `label`, so assistive technology announces the wait. The ring keeps its colour under
 * prefers-reduced-motion; only the turning stops.
 */
export const Spinner: React.FC<SpinnerProps> = ({ label, size = 16, className = '' }) => (
  <span
    role="status"
    aria-label={label}
    className={`${styles.spinner} ${className}`.trim()}
    style={{ width: size, height: size }}
  />
);
