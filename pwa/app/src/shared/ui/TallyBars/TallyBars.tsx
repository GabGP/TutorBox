import React from 'react';
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

const LETTERS = ['A', 'B', 'C', 'D'] as const;

/**
 * Classroom Vote Distribution Horizontal Bar Chart.
 * Visualizes the relative breakdown of student responses across options A, B, C, D
 * with smooth CSS growth transitions and individual vote tallies.
 *
 * @param {TallyBarsProps} props - Component props containing options map, tally counts, total votes, and animation toggle.
 * @returns {JSX.Element} The rendered tally distribution bar chart.
 */
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
      {LETTERS.map((letter) => {
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
