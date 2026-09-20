import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../features/auth/useAuth';
import { resolvePostLoginRedirect } from '../../features/auth/EntryForm';
import { BankPickStep } from './BankPickStep';
import { useRosterManager } from '../../features/roster/useRosterManager';
import { SettingsView } from '../../features/settings/SettingsView';
import { SpeechLanguage } from '../../features/speech/speech.types';
import { getSpeechVoiceKey } from '../../features/speech/speechApi';
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
  const { user, pendingPin, mustChangePin, login, handlePinChange, logout, restoreSession } = useAuth();
  const [voiceLang, setVoiceLang] = useState<SpeechLanguage>(() => {
    const pref = storage.getVoicePreference();
    return pref?.lang === 'quc' ? 'quc' : 'es';
  });
  const [voiceDone, setVoiceDone] = useState(-1);
  // Rounds whose speech already played (auto or manual). Survives remounts
  // (e.g. opening/closing settings) so returning never replays audio.
  const [playedRounds, setPlayedRounds] = useState<number[]>([]);
  const [roleError, setRoleError] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);

  const activeVoiceKey = getSpeechVoiceKey(voiceLang);
  const [prevVoiceKey, setPrevVoiceKey] = useState(activeVoiceKey);

  // When the saved voice changes, allow this round to speak again with the
  // new voice: clear the played guard so autoplay re-runs through the
  // preparation (loading) stage instead of jumping straight to replay.
  useEffect(() => {
    if (prevVoiceKey !== activeVoiceKey) {
      setPrevVoiceKey(activeVoiceKey);
      setPlayedRounds([]);
      setVoiceDone(-1);
    }
  }, [activeVoiceKey, prevVoiceKey]);

  const isStaff = Boolean(user && ['teacher', 'admin'].includes(user.role));
  const initialSid = storage.getTeacherSessionId();
  const coordinator = useTeacherCoordinator(initialSid, { enabled: isStaff, voiceLang });
  const { students, users, deleted, showDeleted, error: rosterErr, pinNotice, addStudent, resetStudentPin, deleteStudent, changeUserRole, recoverStudent, toggleDeleted } = useRosterManager({
    enabled: isStaff,
  });
  const creatableRoles =
    user?.role === 'admin' ? ['student', 'teacher', 'admin'] : ['student', 'teacher'];

  const { state: speechState, message: speechMsg, speak, prefetch, stopPlayback } = useSpeechPlayback(
    coordinator.sid,
    voiceLang
  );

  const curRound = coordinator.session?.current_round;

  useEffect(() => {
    if (curRound?.status === 'closed') {
      void prefetch(curRound.round_index);
    }
  }, [curRound?.round_id, curRound?.status, curRound?.round_index, prefetch]);

  useEffect(() => {
    if (!user) setShowSettings(false);
  }, [user]);

  useEffect(() => {
    setPlayedRounds([]);
  }, [coordinator.sid]);

  useEffect(() => {
    if (!user) return;
    const target =
      typeof window !== 'undefined'
        ? resolvePostLoginRedirect(user.role, window.location.pathname)
        : null;
    if (target) {
      // Students belong on /alumno/ — redirect keeping their session.
      window.location.href = target;
    } else if (!['teacher', 'admin'].includes(user.role)) {
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

  const handlePlaySpeech = useCallback(() => {
    if (curRound) {
      setPlayedRounds((prev) =>
        prev.includes(curRound.round_index) ? prev : [...prev, curRound.round_index]
      );
      speak(curRound.round_index);
    }
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

  const handleCloseSettings = useCallback(() => {
    const pref = storage.getVoicePreference();
    if (pref?.lang && (pref.lang === 'es' || pref.lang === 'quc') && pref.lang !== voiceLang) {
      setVoiceLang(pref.lang as SpeechLanguage);
    }
    const currentKey = getSpeechVoiceKey((pref?.lang as SpeechLanguage) || voiceLang);
    if (prevVoiceKey !== currentKey) {
      setPrevVoiceKey(currentKey);
      setPlayedRounds([]);
      setVoiceDone(-1);
    }
    setShowSettings(false);
  }, [voiceLang, prevVoiceKey]);

  if (!user || !['teacher', 'admin'].includes(user.role) || mustChangePin) {
    return <TeacherAuthView mustChangePin={mustChangePin} pendingPin={pendingPin} roleError={roleError} onLogin={async (u, p) => (setRoleError(null), login(u, p))} onPinChange={handlePinChange} />;
  }

  const [subtitle, title] = TEACHER_STEP_TITLES[step] || ['TutorBox', 'Panel'];
  const isLast = (coordinator.session?.current_round_index ?? 0) + 1 >= (coordinator.session?.question_count ?? 0);
  const isBankSource = step === 'count' && coordinator.source === 'bank';
  const isBankEmpty = isBankSource && coordinator.bankIds.length === 0;
  const primaryText = isBankSource
    ? coordinator.bankIds.length > 0
      ? `Jugar con ${coordinator.bankIds.length}`
      : 'Elige preguntas del banco'
    : getPrimaryActionLabel(step, coordinator.isGenerating, curRound?.status === 'closed', isLast);
  const secondaryText = SECONDARY_ACTION_LABELS[step];
  const wizardIdx = ['topic', 'count', 'lobby'].indexOf(step);

  return (
    <div className={styles.shell} id="shell">
      <TeacherHeader
        title={showSettings ? 'Ajustes' : title}
        subtitle={showSettings ? 'Tu cuenta y opciones' : subtitle}
        step={step}
        voiceLang={voiceLang}
        onBack={() => coordinator.setWizard('topic')}
        onToggleVoice={() => setVoiceLang((v) => (v === 'es' ? 'quc' : 'es'))}
        onOpenSettings={() => setShowSettings(true)}
      />
      {showSettings && user ? (
        <main className={styles.mainContent}>
          <SettingsView
            user={user}
            onProfileChanged={restoreSession}
            onSessionInvalidated={logout}
            onClose={handleCloseSettings}
            bankEnabled={isStaff}
            roster={{
              users, error: rosterErr, pinNotice, onAddStudent: addStudent, onResetPin: resetStudentPin,
              creatableRoles, deleted, showDeleted, onDeleteUser: deleteStudent,
              onRecoverUser: recoverStudent, onToggleDeleted: toggleDeleted,
              onRoleChange: changeUserRole,
            }}
          />
        </main>
      ) : (
        <>
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
        voicePlayed={
          curRound ? playedRounds.includes(curRound.round_index) : false
        }
        voiceLang={voiceLang}
        speechState={speechState}
        speechMessage={speechMsg}
        report={coordinator.report}
        history={coordinator.history}
        onSelectTopic={coordinator.setTopic}
        onChangeCount={coordinator.setCount}
        onPlaySpeech={handlePlaySpeech}
        onSkipSpeech={handleSkipSpeech}
        source={coordinator.source}
        onSourceChange={coordinator.setSource}
        bankStep={
          <BankPickStep
            selectedTopic={coordinator.topic}
            count={coordinator.count}
            onChangeCount={coordinator.setCount}
            genError={coordinator.genError}
            progress={coordinator.progress}
            pregenerating={coordinator.isGenerating}
            bankIds={coordinator.bankIds}
            onToggleBankId={coordinator.toggleBankId}
            onEnsureBankIds={coordinator.ensureBankIds}
            onPregenerate={coordinator.pregenerate}
            isAdmin={user?.role === 'admin'}
          />
        }
      />
      <TeacherFooter
        primaryText={primaryText}
        secondaryText={secondaryText}
        isPrimaryDisabled={coordinator.isGenerating || isBankEmpty || (step === 'lobby' && !coordinator.session)}
        isLobbySuccess={step === 'lobby' && Boolean(coordinator.session)}
        wizardIndex={wizardIdx}
        onPrimary={handlePrimary}
        onSecondary={handleSecondary}
      />
        </>
      )}
    </div>
  );
};
