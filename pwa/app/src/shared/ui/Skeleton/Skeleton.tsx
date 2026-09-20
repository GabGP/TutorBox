import React from 'react';
import styles from './Skeleton.module.css';

export interface SkeletonProps {
  /** Extra sizing (width/height) via inline style or className. */
  className?: string;
  style?: React.CSSProperties;
  /** Accessible label; skeleton is aria-hidden by default (loading state
   * belongs on the container via aria-busy). */
  ariaLabel?: string;
}

/**
 * Generic loading placeholder (shadcn `skeleton` pattern, no dep):
 * pulsing rounded block in token colors. Compose rows of these for
 * table/list loading states so layout never collapses.
 */
export const Skeleton: React.FC<SkeletonProps> = ({
  className = '',
  style,
  ariaLabel,
}) => (
  <span
    className={`${styles.skeleton} ${className}`}
    style={style}
    aria-hidden={ariaLabel ? 'false' : 'true'}
    aria-label={ariaLabel}
  />
);
