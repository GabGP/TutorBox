import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useAuth } from '../../features/auth/useAuth';
import { resolvePostLoginRedirect } from '../../features/auth/EntryForm';
import { BankPickStep } from './BankPickStep';
import { useRosterManager } from '../../features/roster/useRosterManager';
import { TeacherSettingsSheet } from './TeacherSettingsSheet';
import type { SettingsSectionId } from '../../features/settings/SettingsView';
import { ClickerFleetSheet } from '../../features/clickers/ClickerFleetSheet';
import { ReportsView } from '../../features/reports/ReportsView';
import { SystemHealthSheet } from '../../features/system-health/SystemHealthSheet';
import { Sheet } from '../../shared/ui/Sheet/Sheet';
import { ToastViewport } from '../../shared/ui/Toast/ToastViewport';
import { useErrorToast } from '../../shared/ui/Toast/useErrorToast';
import { ApiError } from '../../shared/api/httpClient';
import { SpeechLanguage } from '../../features/speech/speech.types';
import { SPEECH_LANGUAGES, toSpeechLanguage } from '../../features/speech/speechLanguages';
import { getSpeechVoiceKey } from '../../features/speech/speechApi';
import { useSpeechPlayback } from '../../features/speech/useSpeechPlayback';
import { TeacherModeNotice } from '../../features/mode/ModeCards';
import { ModePicker } from '../../features/mode/ModePicker';
import { useApplianceMode } from '../../features/mode/useApplianceMode';
import { TutorRoster } from '../../features/tutor/TutorRoster';
import { storage } from '../../shared/lib/storage';
import { useHostAddress } from '../../shared/routing/session';
import { TeacherAuthView } from './TeacherAuthView';
import { TeacherFooter } from './TeacherFooter';
import { TeacherHeader } from './TeacherHeader';
import { TeacherMainContent } from './TeacherMainContent';
import styles from './TeacherView.module.css';
import { useTeacherCoordinator } from './useTeacherCoordinator';
import { usePlayedRounds } from './usePlayedRounds';
import { getTeacherViewModel } from './teacherViewModel';
import { MODE_HEADER_TITLES } from './teacherViewConfig';

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
    return toSpeechLanguage(pref?.lang);
  });
  const [roleError, setRoleError] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  // Which accordion row the settings sheet opens on (none for the gear button).
  const [settingsSection, setSettingsSection] = useState<SettingsSectionId | undefined>(undefined);
  const [showClickers, setShowClickers] = useState(false);
  const [showReports, setShowReports] = useState(false);
  const [showSystemHealth, setShowSystemHealth] = useState(false);

  const isStaff = Boolean(user && ['teacher', 'admin'].includes(user.role));
  const initialSid = storage.getTeacherSessionId();
  const { users, deleted, showDeleted, pinNotice, toasts, pushToast, dismissToast, addStudent, resetStudentPin, deleteStudent, changeUserRole, recoverStudent, toggleDeleted } = useRosterManager({
    enabled: isStaff,
  });
  // Mode and generation notices float in the same queue as the roster's messages.
  const notices = { pushToast, dismissToast };
  const coordinator = useTeacherCoordinator(initialSid, { enabled: isStaff, voiceLang, notices });
  const { voiceDone, setVoiceDone, markPlayed, hasPlayed, reconcileVoiceKey } =
    usePlayedRounds(coordinator.sid, voiceLang);
  const openSettings = (section?: SettingsSectionId) => {
    setSettingsSection(section);
    setShowSettings(true);
  };
  const creatableRoles =
    user?.role === 'admin' ? ['student', 'teacher', 'admin'] : ['student', 'teacher'];
  // The appliance has no keyboard: this page is the remote that picks the class mode.
  const classMode = useApplianceMode({ enabled: isStaff, notices });
  const mode = classMode.mode ?? 'quiz';
  useErrorToast(classMode.error, pushToast);
  const host = useHostAddress();

  // A voice that could not speak (often out of memory), a failed playback or a blocked
  // autoplay floats as a warning toast; the play button shows every other phase.
  const { state: speechState, speak, prefetch, stopPlayback } = useSpeechPlayback(
    coordinator.sid,
    voiceLang,
    (message) => pushToast({ message, tone: 'warn' })
  );

  const curRound = coordinator.session?.current_round;

  useEffect(() => {
    if (curRound?.status === 'closed') {
      void prefetch(curRound.round_index);
    }
  }, [curRound?.round_id, curRound?.status, curRound?.round_index, prefetch]);

  useEffect(() => {
    if (!user) {
      setShowSettings(false);
      setShowClickers(false);
      setShowReports(false);
      setShowSystemHealth(false);
    }
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
    bankIds: coordinator.bankIds,
    isGenerating: coordinator.isGenerating,
    roundClosed: curRound?.status === 'closed',
    isLast,
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

  // One primary action at a time: a second tap mid-request would skip a question.
  const busyRef = useRef(false);
  const [busy, setBusy] = useState(false);
  const handlePrimary = useCallback(async () => {
    if (busyRef.current) return;
    busyRef.current = true;
    setBusy(true);
    if (step === 'reveal') stopPlayback();
    try {
      await coordinator.advancePrimary();
    } catch (err: unknown) {
      // No answer or a 502/503 from nginx: the backend is restarting, not refusing.
      const restarting = err instanceof ApiError && (err.status === 0 || err.status >= 502);
      pushToast?.({
        message: restarting
          ? "Utz'tutor se está reiniciando. Inténtalo en unos segundos."
          : 'No se pudo avanzar. Inténtalo otra vez.',
        tone: 'error',
      });
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
  }, [step, stopPlayback, coordinator, pushToast]);

  const handleSecondary = useCallback(() => {
    stopPlayback();
    if (step === 'stats') coordinator.resetSession();
    // Lobby or a started match: the server ends it, so phones and the screen leave too.
    else void coordinator.cancelMatch();
  }, [step, stopPlayback, coordinator]);

  const handleCloseSettings = useCallback(() => {
    const pref = storage.getVoicePreference();
    if (pref?.lang && SPEECH_LANGUAGES.includes(pref.lang as SpeechLanguage) && pref.lang !== voiceLang) {
      setVoiceLang(pref.lang as SpeechLanguage);
    }
    const currentKey = getSpeechVoiceKey((pref?.lang as SpeechLanguage) || voiceLang);
    reconcileVoiceKey(currentKey);
    setShowSettings(false);
  }, [voiceLang, reconcileVoiceKey]);

  if (!user || !['teacher', 'admin'].includes(user.role) || mustChangePin) {
    return <TeacherAuthView mustChangePin={mustChangePin} pendingPin={pendingPin} roleError={roleError} onLogin={async (u, p) => (setRoleError(null), login(u, p))} onPinChange={handlePinChange} />;
  }

  const { primaryText, secondaryText, wizardIdx } = vm;
  // The top bar follows the class mode: the quiz steps mean nothing in tutor or take-home mode.
  const [subtitle, title] = mode === 'quiz' ? [vm.subtitle, vm.title] : MODE_HEADER_TITLES[mode];
  // Offer the switch whenever no game is running (the backend also refuses it mid-game).
  const showModePicker = mode !== 'quiz' || step === 'topic' || step === 'stats';

  return (
    <div className={styles.shell} id="shell">
      <TeacherHeader
        title={title}
        subtitle={subtitle}
        canGoBack={mode === 'quiz' && (step === 'count' || step === 'lobby')}
        onBack={step === 'lobby' ? () => void coordinator.backToBankPick() : () => coordinator.setWizard('topic')}
        onOpenSettings={() => openSettings()}
        onOpenClickers={() => setShowClickers(true)}
        onOpenReports={() => setShowReports(true)}
        onOpenSystemHealth={() => setShowSystemHealth(true)}
      />
      {showModePicker && (
        <ModePicker
          mode={classMode.mode}
          saving={classMode.saving}
          pendingMode={classMode.pendingMode}
          onChange={classMode.setMode}
        />
      )}
      {mode !== 'quiz' ? (
        <main className={styles.mainContent}>
          <TeacherModeNotice mode={mode} host={host} />
          {mode === 'tutor' && <TutorRoster host={host} />}
        </main>
      ) : (
        <>
          <TeacherMainContent
            step={step}
            session={coordinator.session}
            currentRound={curRound}
            quiz={{
              topics: coordinator.topics,
              selectedTopic: coordinator.topic,
              bankStep: (
                <BankPickStep
                  selectedTopic={coordinator.topic}
                  count={coordinator.count}
                  onChangeCount={coordinator.setCount}
                  genError={coordinator.genError}
                  progress={coordinator.progress}
                  generating={coordinator.isGenerating}
                  generationPaused={coordinator.isGenerationPaused}
                  onStopGeneration={coordinator.stopGeneration}
                  onResumeGeneration={coordinator.resumeGeneration}
                  onCancelGeneration={coordinator.cancelBankGeneration}
                  onGenerateMore={coordinator.clearGenerationResult}
                  bankIds={coordinator.bankIds}
                  onToggleBankId={coordinator.toggleBankId}
                  onEnsureBankIds={coordinator.ensureBankIds}
                  onGenerate={coordinator.generateIntoBank}
                  isAdmin={user?.role === 'admin'}
                />
              ),
              onSelectTopic: coordinator.setTopic,
            }}
            lobby={{
              onManageUsers: () => openSettings('usuarios'),
              onOpenClickers: () => setShowClickers(true),
            }}
            voice={{
              done: voiceDone,
              played: curRound ? hasPlayed(curRound.round_index) : false,
              lang: voiceLang,
              state: speechState,
              onPlay: handlePlaySpeech,
              onSkip: handleSkipSpeech,
            }}
            outcome={{
              report: coordinator.report,
              history: coordinator.history,
            }}
          />
          <TeacherFooter
            primaryText={primaryText}
            secondaryText={secondaryText}
            isSecondaryHold={vm.isSecondaryHold}
            isPrimaryDisabled={vm.isPrimaryDisabled || busy}
            isLobbySuccess={vm.isLobbySuccess}
            wizardIndex={wizardIdx}
            onPrimary={handlePrimary}
            onSecondary={handleSecondary}
            onHoldTap={(hint) => pushToast?.({ message: hint, tone: 'warn' })}
          />
        </>
      )}
      {showSettings && user && (
        <TeacherSettingsSheet
          user={user}
          onProfileChanged={restoreSession}
          onSessionInvalidated={logout}
          onLogout={() => void logout()}
          onClose={handleCloseSettings}
          staffEnabled={isStaff}
          initialSection={settingsSection}
          roster={{
            users, pinNotice, onAddStudent: addStudent, onResetPin: resetStudentPin,
            creatableRoles, deleted, showDeleted, onDeleteUser: deleteStudent,
            onRecoverUser: recoverStudent, onToggleDeleted: toggleDeleted,
            onRoleChange: changeUserRole,
          }}
        />
      )}
      {showClickers && isStaff && <ClickerFleetSheet onClose={() => setShowClickers(false)} />}
      {showSystemHealth && isStaff && <SystemHealthSheet onClose={() => setShowSystemHealth(false)} />}
      {showReports && isStaff && (
        <Sheet label="Reportes" onClose={() => setShowReports(false)}>
          <ReportsView />
        </Sheet>
      )}
      <ToastViewport toasts={toasts ?? []} onDismiss={(id) => dismissToast?.(id)} />
    </div>
  );
};
