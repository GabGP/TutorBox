import React, { useEffect, useMemo, useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { AccountCard } from '../../features/auth/AccountCard';
import { EntryForm, resolvePostLoginRedirect } from '../../features/auth/EntryForm';
import { ForcedPinModal } from '../../features/auth/ForcedPinModal';
import { useAuth } from '../../features/auth/useAuth';
import { computeStudentStep } from '../../features/session-engine/sessionStateMachine';
import { useSessionEngine } from '../../features/session-engine/useSessionEngine';
import { useStudentVoting } from '../../features/voting/useStudentVoting';
import type { OptionLetter } from '../../shared/constants/options';
import { useOptionKeyboard } from '../../shared/lib/keyboard';
import { storage } from '../../shared/lib/storage';
import { MoodType, useBodyMood } from '../../shared/lib/useBodyMood';
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
  const lastSessionId = storage.getLastStudentSessionId();
  const targetSessionId = useMemo(
    () =>
      typeof window !== 'undefined'
        ? new URLSearchParams(window.location.search).get('s')
        : null,
    []
  );

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
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <button
              type="button"
              className={styles.logoutBtn}
              style={{ alignSelf: 'flex-start', height: '40px', padding: '0 18px', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
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
        selectedOption={currentVote as OptionLetter}
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
        <span>
          <i className={styles.statusDot} />
          {user ? (
            <button
              id="who"
              className={styles.logoutBtn}
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
