import { RoundModel, SessionModel } from './session.types';

export type DisplayStep = 'idle' | 'question' | 'reveal' | 'stats';

/**
 * Computes the deterministic view step for the HDMI classroom projector display
 * based on session and active round states.
 *
 * @param {SessionModel | null} session - Current session snapshot.
 * @returns {DisplayStep} The corresponding display step ('idle', 'question', 'reveal', 'stats').
 */
export function computeDisplayStep(session: SessionModel | null): DisplayStep {
  if (!session || session.status === 'lobby') {
    return 'idle';
  }
  if (session.status === 'completed') {
    return 'stats';
  }
  const round = session.current_round;
  if (!round || !round.question) {
    return 'idle';
  }
  if (round.status === 'revealed') {
    return 'reveal';
  }
  return 'question';
}

export type StudentStep = 'wait' | 'play' | 'sent' | 'result' | 'final';

/**
 * Computes the student client view step based on session status, round phase,
 * and individual student vote submission history.
 *
 * @param {SessionModel | null} session - Current session snapshot.
 * @param {boolean} hasVotedThisRound - Whether the student has already cast a vote in this round.
 * @returns {StudentStep} The corresponding student view step ('wait', 'play', 'sent', 'result', 'final').
 */
export function computeStudentStep(
  session: SessionModel | null,
  hasVotedThisRound: boolean
): StudentStep {
  if (!session || session.status === 'lobby') {
    return 'wait';
  }
  if (session.status === 'completed') {
    return 'final';
  }
  const round = session.current_round;
  if (!round || !round.question) {
    return 'wait';
  }
  if (round.status === 'revealed') {
    return 'result';
  }
  if (hasVotedThisRound || round.status !== 'open' || round.time_remaining === 0) {
    return 'sent';
  }
  return 'play';
}

/**
 * Evaluates whether an open question round has exhausted its countdown timer
 * and should trigger an automatic server-side close transition.
 *
 * @param {RoundModel | null} [round] - The current round snapshot.
 * @returns {boolean} True if the round is open and time_remaining has reached 0.
 */
export function shouldAutoCloseRound(round?: RoundModel | null): boolean {
  return !!(round && round.status === 'open' && round.time_remaining === 0);
}
