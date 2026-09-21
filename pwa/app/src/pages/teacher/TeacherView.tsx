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
import { useTeacherCoordinator } from './useTeacherCoordinator';
import { usePlayedRounds } from './usePlayedRounds';
import { getTeacherViewModel } from './teacherViewModel';

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
  const [roleError, setRoleError] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);

  const isStaff = Boolean(user && ['teacher', 'admin'].includes(user.role));
  const initialSid = storage.getTeacherSessionId();
  const coordinator = useTeacherCoordinator(initialSid, { enabled: isStaff, voiceLang });
  const { voiceDone, setVoiceDone, markPlayed, hasPlayed, reconcileVoiceKey } =
    usePlayedRounds(coordinator.sid, voiceLang);
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

  const isLast = (coordinator.session?.current_round_index ?? 0) + 1 >= (coordinator.session?.question_count ?? 0);
  const vm = getTeacherViewModel({
    session: coordinator.session,
    wizard: coordinator.wizard,
    source: coordinator.source,
    bankIds: coordinator.bankIds,
    isGenerating: coordinator.isGenerating,
    roundClosed: curRound?.status === 'closed',
    isLast,
    hasSessionForLobby: Boolean(coordinator.session),
  });
  const step = vm.step;

  const handlePlaySpeech = useCallback(() => {
    if (curRound) {
      markPlayed(curRound.round_index);
      speak(curRound.round_index);
    }
  }, [curRound, markPlayed, speak]);

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
    reconcileVoiceKey(currentKey);
    setShowSettings(false);
  }, [voiceLang, reconcileVoiceKey]);

  if (!user || !['teacher', 'admin'].includes(user.role) || mustChangePin) {
    return <TeacherAuthView mustChangePin={mustChangePin} pendingPin={pendingPin} roleError={roleError} onLogin={async (u, p) => (setRoleError(null), login(u, p))} onPinChange={handlePinChange} />;
  }

  const { title, subtitle, primaryText, secondaryText, wizardIdx } = vm;

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
          curRound ? hasPlayed(curRound.round_index) : false
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
        isPrimaryDisabled={vm.isPrimaryDisabled}
        isLobbySuccess={vm.isLobbySuccess}
        wizardIndex={wizardIdx}
        onPrimary={handlePrimary}
        onSecondary={handleSecondary}
      />
        </>
      )}
    </div>
  );
};
