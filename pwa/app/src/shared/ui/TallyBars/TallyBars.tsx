import React from 'react';
import { OPTION_LETTERS } from '../../constants/options';
import styles from './TallyBars.module.css';

export interface TallyBarsProps {
  options: Record<string, string>;
  counts?: Record<string, number> | null;
  totalVotes?: number;
  animate?: boolean;
  theme?: 'light' | 'dark';
  className?: string;
  id?: string;
}

export const TallyBars: React.FC<TallyBarsProps> = ({
  options,
  counts,
  totalVotes = 0,
  animate = false,
  theme = 'light',
  className = '',
  id,
}) => {
  const themeClass = theme === 'dark' ? styles.dark : '';

  return (
    <div
      id={id}
      className={`${styles.bars} ${animate ? styles.grow : ''} ${themeClass} ${className}`}
    >
      {OPTION_LETTERS.map((letter) => {
        const text = options[letter] || '';
        const count = counts ? counts[letter] ?? 0 : null;
        const percentage =
          counts && totalVotes > 0 && count !== null
            ? Math.round((100 * count) / totalVotes)
            : 0;

        const colorClass = styles[`k_${letter}`] || '';

        return (
          <div key={letter} className={styles.bar}>
            <span className={`${styles.letter} ${colorClass}`}>{letter}</span>
            <span className={styles.txt} title={text}>
              {text}
            </span>
            <span className={styles.track}>
              <div
                className={`${styles.fill} ${colorClass}`}
                style={{ width: `${percentage}%` }}
              />
            </span>
            <span className={styles.n}>{count !== null ? count : ''}</span>
          </div>
        );
      })}
    </div>
  );
};
