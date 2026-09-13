import React from 'react';
import styles from './CountdownRing.module.css';

export interface CountdownRingProps {
  remaining?: number | null;
  duration?: number;
  size?: number | string;
  theme?: 'light' | 'dark';
  className?: string;
  id?: string;
}

/**
 * Circular SVG/CSS Countdown Ring Timer.
 * Visualizes remaining seconds with a conical gradient border progress ring,
 * switching to high-urgency orange styling when time remaining is 5 seconds or less.
 *
 * @param {CountdownRingProps} props - Component props controlling duration, remaining seconds, size, and CSS classes.
 * @returns {JSX.Element | null} The rendered countdown ring or null if remaining is nullish.
 */
export const CountdownRing: React.FC<CountdownRingProps> = ({
  remaining,
  duration = 20,
  size,
  theme = 'light',
  className = '',
  id,
}) => {
  if (remaining == null) {
    return null;
  }

  const seconds = Math.ceil(remaining);
  const percentage = duration > 0 ? Math.max(0, Math.min(100, (100 * remaining) / duration)) : 0;
  const isLow = seconds <= 5;
  const themeClass = theme === 'dark' ? styles.dark : '';

  const style: React.CSSProperties = {
    ['--pct' as string]: percentage,
    ...(size ? { width: size, height: size } : {}),
  };

  return (
    <div
      id={id}
      className={`${styles.ring} ${isLow ? styles.low : ''} ${themeClass} ${className}`}
      style={style}
      role="timer"
      aria-live="polite"
      aria-label={`${seconds} segundos restantes`}
    >
      <div className={styles.inner}>{seconds}</div>
    </div>
  );
};
