import React, { useEffect, useMemo } from 'react';
import { ForcedPinModal } from '../../features/auth/ForcedPinModal';
import { LoginForm } from '../../features/auth/LoginForm';
import { useAuth } from '../../features/auth/useAuth';
import { computeStudentStep } from '../../features/session-engine/sessionStateMachine';
import { useSessionEngine } from '../../features/session-engine/useSessionEngine';
import { useStudentVoting } from '../../features/voting/useStudentVoting';
import { OptionLetter } from '../../features/voting/voting.types';
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
  const { user, pendingPin, mustChangePin, login, signupAndLogin, handlePinChange, logout } =
    useAuth();
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
    if (user && ['teacher', 'admin'].includes(user.role)) {
      if (typeof window !== 'undefined') window.location.href = '/maestro/';
    }
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

    if (!user || ['teacher', 'admin'].includes(user.role)) {
      return (
        <LoginForm
          title="Entra al juego"
          subtitle="Escribe tu usuario y tu PIN."
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
          <span id="who">{user ? user.username : 'Sin conexión'}</span>
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
