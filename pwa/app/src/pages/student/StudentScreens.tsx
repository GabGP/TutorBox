import React from 'react';
import { OptionLetter } from '../../features/voting/voting.types';
import { StudentFinalScreen } from './StudentFinalScreen';
import { StudentPlayScreen } from './StudentPlayScreen';
import { StudentResultScreen } from './StudentResultScreen';
import { StudentSentScreen } from './StudentSentScreen';
import { StudentWaitScreen } from './StudentWaitScreen';

export interface StudentScreensProps {
  step: string;
  username: string;
  roundIndex: number;
  questionCount?: number;
  timeRemaining?: number | null;
  durationSeconds?: number;
  question?: {
    question_text: string;
    options: Record<string, string>;
  };
  selectedOption: OptionLetter | null;
  myVote: OptionLetter | null;
  isHit: boolean;
  answer: string;
  why: string;
  score: number;
  onVote: (option: OptionLetter) => void;
}

/**
 * Renders the active classroom game turn screen corresponding to current student step.
 *
 * @param {StudentScreensProps} props - Turn state, active question, and vote callbacks.
 * @returns {JSX.Element | null} The corresponding step screen component.
 */
export const StudentScreens: React.FC<StudentScreensProps> = ({
  step,
  username,
  roundIndex,
  questionCount,
  timeRemaining,
  durationSeconds,
  question,
  selectedOption,
  myVote,
  isHit,
  answer,
  why,
  score,
  onVote,
}) => {
  if (step === 'wait') {
    return <StudentWaitScreen username={username} />;
  }
  if (step === 'play' && question) {
    return (
      <StudentPlayScreen
        roundIndex={roundIndex}
        questionCount={questionCount}
        timeRemaining={timeRemaining}
        durationSeconds={durationSeconds}
        questionText={question.question_text}
        options={question.options}
        selectedOption={selectedOption}
        onVote={onVote}
      />
    );
  }
  if (step === 'sent') {
    return <StudentSentScreen myVote={myVote} />;
  }
  if (step === 'result') {
    return (
      <StudentResultScreen
        isHit={isHit}
        myVote={myVote}
        answer={answer}
        why={why}
        score={score}
        roundIndex={roundIndex}
      />
    );
  }
  if (step === 'final') {
    return (
      <StudentFinalScreen
        score={score}
        questionCount={questionCount}
        username={username}
      />
    );
  }
  return null;
};
