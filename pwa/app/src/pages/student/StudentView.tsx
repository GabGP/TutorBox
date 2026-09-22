import React, { useEffect, useMemo, useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { AccountCard } from '../../features/auth/AccountCard';
import { EntryForm, resolvePostLoginRedirect } from '../../features/auth/EntryForm';
import { ForcedPinModal } from '../../features/auth/ForcedPinModal';
import { useAuth } from '../../features/auth/useAuth';
import { computeStudentStep } from '../../features/session-engine/sessionStateMachine';
import { useSessionEngine } from '../../features/session-engine/useSessionEngine';
import { useStudentVoting } from '../../features/voting/useStudentVoting';
import { getSessionQueryParamId } from '../../features/session-engine/sessionApi';
import { useOptionKeyboard } from '../../shared/lib/keyboard';
import { storage } from '../../shared/lib/storage';
import { MoodType, useBodyMood } from '../../shared/lib/useBodyMood';
import utils from '../../shared/styles/utils.module.css';
import { StudentScreens } from './StudentScreens';
import styles from './StudentView.module.css';

/**
 * Main Student Role View for the classroom mobile web client.
 * Manages authentication, PIN updates, session synchronization, and turn progression.
 */
export const StudentView: React.FC = () => {
  const { user, pendingPin, mustChangePin, login, signupAndLogin, handlePinChange, logout, restoreSession } =
    useAuth();
  const [showAccount, setShowAccount] = useState(false);
  const [lastSessionId, setLastSessionId] = useState<string | null>(null);
  const targetSessionId = useMemo(() => getSessionQueryParamId(), []);

  useEffect(() => {
    setLastSessionId(storage.getLastStudentSessionId());
  }, []);

  const { session } = useSessionEngine({
    targetSessionId: targetSessionId || undefined,
    fallbackSessionId: lastSessionId,
    enabled: Boolean(user),
  });

  const currentRound = session?.current_round;
  const roundId = currentRound?.round_id || null;

  const { votes, currentVote, castVote, recordHit, score } = useStudentVoting(
    session?.id || null,
    roundId,
    logout
  );

  useEffect(() => {
    if (session?.id) {
      storage.setLastStudentSessionId(session.id);
    }
  }, [session?.id]);

  const myVote = roundId ? votes[roundId] : null;
  const isRevealed = currentRound?.status === 'revealed';
  const isHit = Boolean(
    myVote && isRevealed && currentRound?.result?.tally?.correct_option === myVote
  );

  useEffect(() => {
    if (roundId && isRevealed && myVote) recordHit(roundId, isHit);
  }, [roundId, isRevealed, isHit, myVote, recordHit]);

  const step = computeStudentStep(session, Boolean(myVote));
  let mood: MoodType = null;
  if (step === 'final') mood = 'final';
  else if (step === 'result') mood = isHit ? 'good' : 'bad';
  useBodyMood(mood);

  // Header connection indicator: green once the live session is syncing,
  // amber while logged in without a session yet, grey when logged out.
  // Previously the dot was always green, even next to "Sin conexión".
  const connectionState: 'online' | 'idle' | 'offline' = !user
    ? 'offline'
    : session
      ? 'online'
      : 'idle';
  const dotClass =
    connectionState === 'online'
      ? styles.dotOnline
      : connectionState === 'idle'
        ? styles.dotIdle
        : styles.dotOffline;
  const dotLabel =
    connectionState === 'online'
      ? 'Conectado a la sesión'
      : connectionState === 'idle'
        ? 'Esperando la sesión'
        : 'Sin conexión';

  useOptionKeyboard(castVote, step === 'play');

  useEffect(() => {
    if (!user) setShowAccount(false);
  }, [user]);

  useEffect(() => {
    if (typeof window === 'undefined' || !user) return;
    const target = resolvePostLoginRedirect(user.role, window.location.pathname);
    if (target) window.location.href = target;
  }, [user]);

  const q = currentRound?.question;
  const correctOpt = currentRound?.result?.tally?.correct_option;
  const answer = correctOpt && q ? `${correctOpt} · ${q.options[correctOpt]}` : '';
  const why =
    myVote && !isHit && currentRound?.result?.explanations
      ? currentRound.result.explanations[myVote] || ''
      : '';

  const renderContent = () => {
    if (mustChangePin) {
      return <ForcedPinModal currentPin={pendingPin} onPinChange={handlePinChange} />;
    }

    if (showAccount && user) {
      return (
        <div className={styles.accountPanel}>
            <button
              type="button"
              className={`${styles.logoutBtn} ${styles.accountBack} ${utils.rowInline6}`}
              onClick={() => setShowAccount(false)}
            >
              <ArrowLeft size={16} aria-hidden /> Volver al juego
            </button>
          <AccountCard
            user={user}
            onProfileChanged={restoreSession}
            onSessionInvalidated={async () => {
              setShowAccount(false);
              await logout();
            }}
          />
        </div>
      );
    }

    if (!user || ['teacher', 'admin'].includes(user.role)) {
      return (
        <EntryForm
          title="Entra al juego"
          subtitle="Escribe tu usuario y tu PIN. Docentes: usen /maestro/."
          allowSignup
          onLogin={login}
          onSignup={signupAndLogin}
        />
      );
    }

    return (
      <StudentScreens
        step={step}
        username={user.username}
        roundIndex={currentRound?.round_index ?? 0}
        questionCount={session?.question_count}
        timeRemaining={currentRound?.time_remaining}
        durationSeconds={currentRound?.duration_seconds}
        question={q}
        selectedOption={currentVote}
        myVote={myVote}
        isHit={isHit}
        answer={answer}
        why={why}
        score={score}
        onVote={castVote}
      />
    );
  };

  return (
    <div className={styles.studentShell}>
      <header className={styles.header}>
        <span>TutorBox</span>
        <span className={styles.headerActions}>
          <i className={`${styles.statusDot} ${dotClass}`} role="status" aria-label={dotLabel} />
          {user ? (
            <button
              id="who"
              className={`${styles.logoutBtn} ${styles.userBtn}`}
              onClick={() => setShowAccount((v) => !v)}
              title="Mi cuenta"
            >
              {user.username}
            </button>
          ) : (
            <span id="who">Sin conexión</span>
          )}
          {user && (
            <button id="out" className={styles.logoutBtn} onClick={logout}>
              Salir
            </button>
          )}
        </span>
      </header>
      <main className={styles.mainContent}>{renderContent()}</main>
    </div>
  );
};
