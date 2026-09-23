import React from 'react';
import { MatchReportView } from '../../features/match-report/MatchReportView';
import { QuestionCountPicker } from '../../features/question-generator/QuestionCountPicker';
import { TopicSelector } from '../../features/question-generator/TopicSelector';
import { getTopicLabel } from '../../shared/taxonomy/labels';
import { TelemetryView } from '../../features/question-generator/TelemetryView';
import { RosterTableProps } from '../../features/roster/RosterTable';
import { Collapsible } from '../../shared/ui/Collapsible/Collapsible';
import { useHostAddress } from '../../shared/routing/session';
import { QUESTION_SOURCE_OPTIONS, SourceSwitch } from './SourceSwitch';
import { SpeechLanguage, SpeechState } from '../../features/speech/speech.types';
import { RoundModel, SessionModel, SessionReport } from '../../features/session-engine/session.types';
import { GenerationProgress, TopicModel } from '../../features/question-generator/generator.types';
import { StoredRoundHistory } from '../../shared/lib/storage';
import { TeacherLiveRounds } from './TeacherLiveRounds';
import { TeacherLobby } from './TeacherLobby';
import styles from './TeacherView.module.css';

/** Quiz-setup slice: topics, count, generation, bank source. */
export interface QuizSetupProps {
  topics: TopicModel[];
  selectedTopic: string;
  count: number;
  genError?: string | null;
  progress: GenerationProgress | null;
  source: 'generate' | 'bank';
  bankStep: React.ReactNode;
  onSelectTopic: (topic: string) => void;
  onChangeCount: (count: number) => void;
  onSourceChange: (s: 'generate' | 'bank') => void;
}

/** Speech playback slice for live rounds. */
export interface LiveVoiceProps {
  done: number;
  played: boolean;
  lang: SpeechLanguage;
  state: SpeechState;
  message: string;
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
  roster: RosterTableProps;
  voice: LiveVoiceProps;
  outcome: MatchOutcomeProps;
}

/**
 * Teacher Console Step Content Switcher.
 * Renders the active workspace screen: topic selector, question count picker,
 * pre-game lobby, live voting/reveal rounds, or end-of-game match report.
 *
 * @param {TeacherMainContentProps} props - Step state plus the quiz, roster,
 * voice and outcome slices.
 * @returns {JSX.Element} The rendered main content panel.
 */
export const TeacherMainContent: React.FC<TeacherMainContentProps> = ({
  step,
  session,
  currentRound,
  quiz,
  roster,
  voice,
  outcome,
}) => {
  const host = useHostAddress();
  const hostAddress = host ? `${host}/alumno` : '';
  return (
    <main className={styles.mainContent}>
      {step === 'topic' && (
        <section id="s-topic" className={styles.stack}>
          <SourceSwitch
            value={quiz.source}
            onChange={quiz.onSourceChange}
            options={QUESTION_SOURCE_OPTIONS}
            ariaLabel="Origen de preguntas"
          />
          <TopicSelector
            topics={quiz.topics}
            selectedTopic={quiz.selectedTopic}
            onSelectTopic={quiz.onSelectTopic}
          />
        </section>
      )}
      {step === 'count' && quiz.source === 'generate' && (
        <section id="s-count" className={styles.stack}>
          <QuestionCountPicker
            count={quiz.count}
            topicLabel={getTopicLabel(quiz.selectedTopic)}
            onChangeCount={quiz.onChangeCount}
            errorNote={quiz.genError}
          />
          <Collapsible title="Actividad de generación">
            <TelemetryView />
          </Collapsible>
        </section>
      )}
      {step === 'count' && quiz.source === 'bank' && (
        <section id="s-count">{quiz.bankStep}</section>
      )}
      {step === 'lobby' && (
        <TeacherLobby
          session={session}
          progress={quiz.progress}
          hostAddress={hostAddress}
          rosterProps={roster}
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
          speechMessage={voice.message}
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
