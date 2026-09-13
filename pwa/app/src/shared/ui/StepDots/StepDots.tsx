import React from 'react';
import styles from './StepDots.module.css';

export interface StepDotsProps {
  count?: number;
  currentIndex: number;
  className?: string;
  id?: string;
}

/**
 * Wizard Step Progress Indicator Dots.
 * Visualizes progression through multi-step setup wizards (Step 1 -> 2 -> 3)
 * with animated active state highlights.
 *
 * @param {StepDotsProps} props - Component props containing total steps count and current active index.
 * @returns {JSX.Element | null} The rendered step dots or null if index is out of bounds.
 */
export const StepDots: React.FC<StepDotsProps> = ({
  count = 3,
  currentIndex,
  className = '',
  id,
}) => {
  if (currentIndex < 0 || currentIndex >= count) {
    return null;
  }

  const dots = Array.from({ length: count }, (_, i) => i);

  return (
    <div id={id} className={`${styles.dots} ${className}`}>
      {dots.map((i) => {
        const isOn = i <= currentIndex;
        const isCurrent = i === currentIndex;
        return (
          <i
            key={i}
            className={`${styles.dot} ${isOn ? styles.on : ''} ${isCurrent ? styles.cur : ''}`}
          />
        );
      })}
    </div>
  );
};
