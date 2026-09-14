import React from 'react';
import styles from './ProgressBar.module.css';

export interface ProgressBarProps {
  value: number;
  max?: number;
  animated?: boolean;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  id?: string;
  label?: string;
  speed?: number;
  pulseKey?: string | number;
}

/**
 * Accessible progress bar component following shadcn/ui contract with optional animated shimmer.
 */
export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  animated = true,
  showLabel = false,
  size = 'md',
  className,
  id,
  label = 'Progreso',
  speed = 5.5,
  pulseKey,
}) => {
  const safeMax = max > 0 ? max : 100;
  const percentage = Math.min(100, Math.max(0, (value / safeMax) * 100));
  const roundedPercent = Math.round(percentage);

  return (
    <div
      className={`${styles.root} ${styles[size]} ${className || ''}`.trim()}
      id={id}
      style={{ '--speed': `${speed}s` } as React.CSSProperties}
    >
      <div
        className={styles.track}
        role="progressbar"
        aria-valuenow={roundedPercent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label}
      >
        <div
          className={styles.fill}
          style={{ width: `${percentage}%` }}
        />
        {animated && (
          <div
            key={pulseKey}
            className={styles.shimmer}
            data-testid="progress-shimmer"
          />
        )}
      </div>
      {showLabel && (
        <span className={styles.label} data-testid="progress-label">
          {roundedPercent}%
        </span>
      )}
    </div>
  );
};
