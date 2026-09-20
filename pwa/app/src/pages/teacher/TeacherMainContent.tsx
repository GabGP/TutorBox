import React from 'react';
import { MatchReportView } from '../../features/match-report/MatchReportView';
import { QuestionCountPicker } from '../../features/question-generator/QuestionCountPicker';
import { getTopicLabel, TopicSelector } from '../../features/question-generator/TopicSelector';
import { TelemetryView } from '../../features/question-generator/TelemetryView';
import { RosterTableProps } from '../../features/roster/RosterTable';
import { QUESTION_SOURCE_OPTIONS, SourceSwitch } from './SourceSwitch';
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
  voicePlayed: boolean;
  voiceLang: SpeechLanguage;
  speechState: SpeechState;
  speechMessage: string;
  report: SessionReport | null;
  history: StoredRoundHistory[];
  onSelectTopic: (topic: string) => void;
  onChangeCount: (count: number) => void;
  onPlaySpeech: () => void;
  onSkipSpeech: () => void;
  source: 'generate' | 'bank';
  onSourceChange: (s: 'generate' | 'bank') => void;
  bankStep: React.ReactNode;
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
  voicePlayed,
  voiceLang,
  speechState,
  speechMessage,
  report,
  history,
  onSelectTopic,
  onChangeCount,
  onPlaySpeech,
  onSkipSpeech,
  source,
  onSourceChange,
  bankStep,
}) => {
  return (
    <main className={styles.mainContent}>
      {step === 'topic' && (
        <section id="s-topic" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <SourceSwitch
            value={source}
            onChange={onSourceChange}
            options={QUESTION_SOURCE_OPTIONS}
            ariaLabel="Origen de preguntas"
          />
          <TopicSelector
            topics={topics}
            selectedTopic={selectedTopic}
            onSelectTopic={onSelectTopic}
          />
        </section>
      )}
      {step === 'count' && source === 'generate' && (
        <section id="s-count" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <QuestionCountPicker
            count={count}
            topicLabel={getTopicLabel(selectedTopic)}
            onChangeCount={onChangeCount}
            errorNote={genError}
          />
          <details>
            <summary
              style={{ color: 'var(--p)', fontWeight: 600, cursor: 'pointer' }}
            >
              Actividad de generación
            </summary>
            <div style={{ marginTop: '12px' }}>
              <TelemetryView />
            </div>
          </details>
        </section>
      )}
      {step === 'count' && source === 'bank' && (
        <section id="s-count">{bankStep}</section>
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
          voicePlayed={voicePlayed}
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
