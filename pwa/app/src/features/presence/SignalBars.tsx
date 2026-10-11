import React from 'react';
import styles from './presence.module.css';
import type { SignalStrength } from './presence.types';
import { signalLabel } from './presenceLabels';

/** How many of the three bars are lit for each strength. */
const LIT_BARS: Record<SignalStrength, number> = { good: 3, fair: 2, weak: 1 };

export interface SignalBarsProps {
  signal: SignalStrength;
}

/**
 * Three rising bars for a clicker's radio signal. The image role and the
 * label carry the strength to screen readers; the bars are only a picture.
 */
export const SignalBars: React.FC<SignalBarsProps> = ({ signal }) => {
  const litCount = LIT_BARS[signal];
  return (
    <span className={styles.signal} role="img" aria-label={signalLabel(signal)}>
      {[1, 2, 3].map((barNumber) => (
        <span
          key={barNumber}
          className={barNumber <= litCount ? `${styles.bar} ${styles.barLit}` : styles.bar}
        />
      ))}
    </span>
  );
};
