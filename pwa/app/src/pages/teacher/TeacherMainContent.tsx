import React from 'react';
import { MatchReportView } from '../../features/match-report/MatchReportView';
import { QuestionCountPicker } from '../../features/question-generator/QuestionCountPicker';
import { getTopicLabel, TopicSelector } from '../../features/question-generator/TopicSelector';
import { RosterTableProps } from '../../features/roster/RosterTable';
import { SpeechLanguage, SpeechState } from '../../features/speech/speech.types';
import { RoundModel, SessionModel, SessionReport } from '../../features/session-engine/session.types';
import { GenerationProgress, TopicModel } from '../../features/question-generator/generator.types';
import { StoredRoundHistory } from '../../shared/lib/storage';
import { TeacherLiveRounds } from './TeacherLiveRounds';
import { TeacherLobby } from './TeacherLobby';
import styles from './TeacherView.module.css';

export interface TeacherMainContentProps {
  step: string;
  session: SessionModel | null;
  currentRound?: RoundModel | null;
  topics: TopicModel[];
  selectedTopic: string;
  count: number;
  genError?: string | null;
  progress: GenerationProgress | null;
  rosterProps: RosterTableProps;
  voiceDone: number;
  voiceLang: SpeechLanguage;
  speechState: SpeechState;
  speechMessage: string;
  report: SessionReport | null;
  history: StoredRoundHistory[];
  onSelectTopic: (topic: string) => void;
  onChangeCount: (count: number) => void;
  onPlaySpeech: () => void;
  onSkipSpeech: () => void;
}

/**
 * Teacher Console Step Content Switcher.
 * Renders the active workspace screen: topic selector, question count picker,
 * pre-game lobby, live voting/reveal rounds, or end-of-game match report.
 *
 * @param {TeacherMainContentProps} props - Component props containing current step state and callbacks.
 * @returns {JSX.Element} The rendered main content panel.
 */
export const TeacherMainContent: React.FC<TeacherMainContentProps> = ({
  step,
  session,
  currentRound,
  topics,
  selectedTopic,
  count,
  genError,
  progress,
  rosterProps,
  voiceDone,
  voiceLang,
  speechState,
  speechMessage,
  report,
  history,
  onSelectTopic,
  onChangeCount,
  onPlaySpeech,
  onSkipSpeech,
}) => {
  return (
    <main className={styles.mainContent}>
      {step === 'topic' && (
        <section id="s-topic">
          <TopicSelector
            topics={topics}
            selectedTopic={selectedTopic}
            onSelectTopic={onSelectTopic}
          />
        </section>
      )}
      {step === 'count' && (
        <section id="s-count">
          <QuestionCountPicker
            count={count}
            topicLabel={getTopicLabel(selectedTopic)}
            onChangeCount={onChangeCount}
            errorNote={genError}
          />
        </section>
      )}
      {step === 'lobby' && (
        <TeacherLobby
          session={session}
          progress={progress}
          hostAddress={typeof window !== 'undefined' ? `${window.location.host}/alumno` : ''}
          rosterProps={rosterProps}
        />
      )}
      {(step === 'question' || step === 'reveal') && session && currentRound && (
        <TeacherLiveRounds
          step={step}
          session={session}
          round={currentRound}
          voiceDone={voiceDone}
          voiceLang={voiceLang}
          speechState={speechState}
          speechMessage={speechMessage}
          onPlaySpeech={onPlaySpeech}
          onSkipSpeech={onSkipSpeech}
        />
      )}
      {step === 'stats' && (
        <section id="s-stats">
          <MatchReportView report={report} history={history} />
        </section>
      )}
    </main>
  );
};
