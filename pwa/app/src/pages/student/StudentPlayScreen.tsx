import React from 'react';
import { StudentVoteGrid } from '../../features/voting/StudentVoteGrid';
import type { OptionLetter } from '../../shared/constants/options';
import { CountdownRing } from '../../shared/ui/CountdownRing/CountdownRing';
import styles from './StudentView.module.css';

export interface StudentPlayScreenProps {
  roundIndex: number;
  questionCount?: number;
  timeRemaining?: number | null;
  durationSeconds?: number;
  questionText: string;
  options: Record<string, string>;
  selectedOption?: OptionLetter | null;
  onVote: (letter: OptionLetter) => void;
}

/**
 * Active multiple-choice question screen for student voting.
 *
 * @param {StudentPlayScreenProps} props - Component props containing round details, timer, options, and vote callback.
 * @returns {JSX.Element} The rendered active student question screen.
 */
export const StudentPlayScreen: React.FC<StudentPlayScreenProps> = ({
  roundIndex,
  questionCount = 0,
  timeRemaining,
  durationSeconds,
  questionText,
  options,
  selectedOption,
  onVote,
}) => {
  return (
    <section id="s-play" className={styles.section}>
      <div className={styles.top}>
        <span id="counter">
          Pregunta {roundIndex + 1} de {questionCount}
        </span>
        <CountdownRing
          id="ring"
          size={46}
          remaining={timeRemaining}
          duration={durationSeconds}
        />
      </div>
      <div className={styles.q} id="qtext">
        {questionText}
      </div>
      <StudentVoteGrid
        options={options}
        selectedOption={selectedOption}
        onVote={onVote}
      />
    </section>
  );
};
