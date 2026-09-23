import React from 'react';
import { OptionTile } from '../../shared/ui/OptionTile/OptionTile';
import styles from './voting.module.css';
import { OPTION_LETTERS, type OptionLetter } from '../../shared/constants/options';

export type { OptionLetter } from '../../shared/constants/options';

export interface StudentVoteGridProps {
  options: Record<string, string>;
  selectedOption?: OptionLetter | null;
  onVote: (letter: OptionLetter) => void;
  disabled?: boolean;
}

export const StudentVoteGrid: React.FC<StudentVoteGridProps> = ({
  options,
  selectedOption,
  onVote,
  disabled = false,
}) => {
  const isLocked = Boolean(selectedOption) || disabled;

  return (
    <div className={styles.tiles} id="tiles">
      {OPTION_LETTERS.map((letter) => (
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
