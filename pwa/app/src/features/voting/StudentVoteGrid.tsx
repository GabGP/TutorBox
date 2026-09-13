import React from 'react';
import { OptionTile } from '../../shared/ui/OptionTile/OptionTile';
import styles from './voting.module.css';
import { OptionLetter } from './voting.types';

export interface StudentVoteGridProps {
  options: Record<string, string>;
  selectedOption?: OptionLetter | null;
  onVote: (letter: OptionLetter) => void;
  disabled?: boolean;
}

const LETTERS: OptionLetter[] = ['A', 'B', 'C', 'D'];

/**
 * Student Voting Option 2x2 Grid component.
 * Renders multiple-choice options (A, B, C, D) with high-contrast colored tiles,
 * touch targets, keyboard navigation shortcuts, and vote-locking indicators.
 *
 * @param {StudentVoteGridProps} props - Component props containing options dictionary, selection status, and vote callback.
 * @returns {JSX.Element} The rendered 2x2 response options grid.
 */
export const StudentVoteGrid: React.FC<StudentVoteGridProps> = ({
  options,
  selectedOption,
  onVote,
  disabled = false,
}) => {
  const isLocked = Boolean(selectedOption) || disabled;

  return (
    <div className={styles.tiles} id="tiles">
      {LETTERS.map((letter) => (
        <OptionTile
          key={letter}
          letter={letter}
          text={options[letter] || ''}
          isPicked={selectedOption === letter}
          isLocked={isLocked}
          onSelect={onVote}
          disabled={disabled}
        />
      ))}
    </div>
  );
};
