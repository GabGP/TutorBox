import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../features/auth/useAuth';
import { useRosterManager } from '../../features/roster/useRosterManager';
import { SpeechLanguage } from '../../features/speech/speech.types';
import { useSpeechPlayback } from '../../features/speech/useSpeechPlayback';
import { storage } from '../../shared/lib/storage';
import { TeacherAuthView } from './TeacherAuthView';
import { TeacherFooter } from './TeacherFooter';
import { TeacherHeader } from './TeacherHeader';
import { TeacherMainContent } from './TeacherMainContent';
import styles from './TeacherView.module.css';
import {
  getPrimaryActionLabel,
  SECONDARY_ACTION_LABELS,
  TEACHER_STEP_TITLES,
} from './teacherViewConfig';
import { useTeacherCoordinator } from './useTeacherCoordinator';

/**
 * Teacher Console Master View.
 * Coordinates match creation, topic selection, real-time live round management,
 * offline speech playback triggering, and post-match pedagogical reports.
 *
 * @returns {JSX.Element} The rendered teacher console interface.
 */
export const TeacherView: React.FC = () => {
  const { user, pendingPin, mustChangePin, login, handlePinChange, logout } = useAuth();
  const [voiceLang, setVoiceLang] = useState<SpeechLanguage>('es');
  const [voiceDone, setVoiceDone] = useState(-1);
  const [roleError, setRoleError] = useState<string | null>(null);

  const isStaff = Boolean(user && ['teacher', 'admin'].includes(user.role));
  const initialSid = storage.getTeacherSessionId();
  const coordinator = useTeacherCoordinator(initialSid, { enabled: isStaff });
  const { students, error: rosterErr, pinNotice, addStudent, resetStudentPin } = useRosterManager({
    enabled: isStaff,
  });

  const { state: speechState, message: speechMsg, speak, stopPlayback } = useSpeechPlayback(
    coordinator.sid,
    voiceLang
  );

  useEffect(() => {
    if (user && !['teacher', 'admin'].includes(user.role)) {
      logout();
      setRoleError('Esta página es para docentes. Los alumnos entran en /alumno/');
    }
  }, [user, logout]);

  let step: string = coordinator.session ? 'lobby' : coordinator.wizard;
  if (coordinator.session?.status === 'active') {
    step = coordinator.session.current_round?.status === 'revealed' ? 'reveal' : 'question';
  } else if (coordinator.session?.status === 'completed') {
    step = 'stats';
  }

  const curRound = coordinator.session?.current_round;

  const handlePlaySpeech = useCallback(() => {
    if (curRound) speak(curRound.round_index);
  }, [curRound, speak]);

  const handleSkipSpeech = useCallback(() => {
    stopPlayback();
    if (speechState !== 'loading' && speechState !== 'playing' && curRound) {
      setVoiceDone(curRound.round_index);
    }
  }, [curRound, speechState, stopPlayback]);

  const handlePrimary = useCallback(() => {
    if (step === 'reveal') stopPlayback();
    coordinator.advancePrimary();
  }, [step, stopPlayback, coordinator]);

  const handleSecondary = useCallback(() => {
    stopPlayback();
    if (step === 'topic') logout();
    else coordinator.resetSession();
  }, [step, stopPlayback, logout, coordinator]);

  if (!user || !['teacher', 'admin'].includes(user.role) || mustChangePin) {
    return (
      <TeacherAuthView
        mustChangePin={mustChangePin}
        pendingPin={pendingPin}
        roleError={roleError}
        onLogin={async (u, p) => (setRoleError(null), login(u, p))}
        onPinChange={handlePinChange}
      />
    );
  }

  const [subtitle, title] = TEACHER_STEP_TITLES[step] || ['TutorBox', 'Panel'];
  const isLast = (coordinator.session?.current_round_index ?? 0) + 1 >= (coordinator.session?.question_count ?? 0);
  const isClosed = curRound?.status === 'closed';

  const primaryText = getPrimaryActionLabel(step, coordinator.isGenerating, isClosed, isLast);
  const secondaryText = SECONDARY_ACTION_LABELS[step];
  const wizardIdx = ['topic', 'count', 'lobby'].indexOf(step);

  return (
    <div className={styles.shell} id="shell">
      <TeacherHeader
        title={title}
        subtitle={subtitle}
        step={step}
        voiceLang={voiceLang}
        onBack={() => coordinator.setWizard('topic')}
        onToggleVoice={() => setVoiceLang((v) => (v === 'es' ? 'quc' : 'es'))}
      />
      <TeacherMainContent
        step={step}
        session={coordinator.session}
        currentRound={curRound}
        topics={coordinator.topics}
        selectedTopic={coordinator.topic}
        count={coordinator.count}
        genError={coordinator.genError}
        progress={coordinator.progress}
        rosterProps={{
          students, error: rosterErr, pinNotice, onAddStudent: addStudent, onResetPin: resetStudentPin,
        }}
        voiceDone={voiceDone}
        voiceLang={voiceLang}
        speechState={speechState}
        speechMessage={speechMsg}
        report={coordinator.report}
        history={coordinator.history}
        onSelectTopic={coordinator.setTopic}
        onChangeCount={coordinator.setCount}
        onPlaySpeech={handlePlaySpeech}
        onSkipSpeech={handleSkipSpeech}
      />
      <TeacherFooter
        primaryText={primaryText}
        secondaryText={secondaryText}
        isPrimaryDisabled={coordinator.isGenerating || (step === 'lobby' && !coordinator.session)}
        isLobbySuccess={step === 'lobby' && Boolean(coordinator.session)}
        wizardIndex={wizardIdx}
        onPrimary={handlePrimary}
        onSecondary={handleSecondary}
      />
    </div>
  );
};
