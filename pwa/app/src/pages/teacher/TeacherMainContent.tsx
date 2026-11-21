import React from 'react';
import { MatchReportView } from '../../features/match-report/MatchReportView';
import { TopicSelector } from '../../features/question-generator/TopicSelector';
import { useHostAddress } from '../../shared/routing/session';
import { SpeechLanguage, SpeechState } from '../../features/speech/speech.types';
import { RoundModel, SessionModel, SessionReport } from '../../features/session-engine/session.types';
import { TopicModel } from '../../features/question-generator/generator.types';
import { StoredRoundHistory } from '../../shared/lib/storage';
import { TeacherLiveRounds } from './TeacherLiveRounds';
import { TeacherLobby } from './TeacherLobby';
import styles from './TeacherView.module.css';

/** Quiz-setup slice: topic choice, then the bank step (pick, write or generate). */
export interface QuizSetupProps {
  topics: TopicModel[];
  selectedTopic: string;
  bankStep: React.ReactNode;
  onSelectTopic: (topic: string) => void;
}

/** Speech playback slice for live rounds. */
export interface LiveVoiceProps {
  done: number;
  played: boolean;
  lang: SpeechLanguage;
  state: SpeechState;
  onPlay: () => void;
  onSkip: () => void;
}

/** Post-match outcome slice. */
export interface MatchOutcomeProps {
  report: SessionReport | null;
  history: StoredRoundHistory[];
}

export interface TeacherMainContentProps {
  step: string;
  session: SessionModel | null;
  currentRound?: RoundModel | null;
  quiz: QuizSetupProps;
  lobby: { onManageUsers: () => void; onOpenClickers: () => void };
  voice: LiveVoiceProps;
  outcome: MatchOutcomeProps;
}

/**
 * Teacher Console Step Content Switcher.
 * Renders the active workspace screen: topic selector, bank step (pick, write or generate),
 * pre-game lobby, live voting/reveal rounds, or end-of-game match report.
 *
 * @param {TeacherMainContentProps} props - Step state plus the quiz, lobby,
 * voice and outcome slices.
 * @returns {JSX.Element} The rendered main content panel.
 */
export const TeacherMainContent: React.FC<TeacherMainContentProps> = ({
  step,
  session,
  currentRound,
  quiz,
  lobby,
  voice,
  outcome,
}) => {
  const host = useHostAddress();
  const hostAddress = host ? `${host}/alumno` : '';
  return (
    <main className={styles.mainContent}>
      {step === 'topic' && (
        <section id="s-topic" className={styles.stack}>
          <TopicSelector
            topics={quiz.topics}
            selectedTopic={quiz.selectedTopic}
            onSelectTopic={quiz.onSelectTopic}
          />
        </section>
      )}
      {step === 'count' && <section id="s-count">{quiz.bankStep}</section>}
      {step === 'lobby' && (
        <TeacherLobby
          session={session}
          hostAddress={hostAddress}
          onManageUsers={lobby.onManageUsers}
          onOpenClickers={lobby.onOpenClickers}
        />
      )}
      {(step === 'question' || step === 'reveal') && session && currentRound && (
        <TeacherLiveRounds
          step={step}
          session={session}
          round={currentRound}
          voiceDone={voice.done}
          voicePlayed={voice.played}
          voiceLang={voice.lang}
          speechState={voice.state}
          onPlaySpeech={voice.onPlay}
          onSkipSpeech={voice.onSkip}
        />
      )}
      {step === 'stats' && (
        <section id="s-stats">
          <MatchReportView report={outcome.report} history={outcome.history} />
        </section>
      )}
    </main>
  );
};
