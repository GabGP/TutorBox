import { describe, expect, it } from 'vitest';
import {
  computeDisplayStep,
  computeStudentStep,
  shouldAutoCloseRound,
} from '../sessionStateMachine';
import { RoundModel, SessionModel } from '../session.types';

describe('Two-Tier Session State Machine', () => {
  const baseSession: SessionModel = {
    id: 's1',
    title: 'Test Session',
    topic: 'arithmetic',
    status: 'lobby',
    question_count: 5,
    current_round_index: 0,
    created_at: new Date().toISOString(),
  };

  const baseRound: RoundModel = {
    round_id: 'r1',
    round_index: 0,
    duration_seconds: 20,
    time_remaining: 15,
    status: 'open',
    votes_cast: 2,
    question: {
      id: 'q1',
      question_text: '¿Cuánto es 5 * 5?',
      options: { A: '25', B: '20', C: '15', D: '30' },
    },
  };

  describe('computeDisplayStep', () => {
    it('resolves idle when session is in lobby or null', () => {
      expect(computeDisplayStep(null)).toBe('idle');
      expect(computeDisplayStep(baseSession)).toBe('idle');
    });

    it('resolves question when round is open or closed', () => {
      const activeSession: SessionModel = {
        ...baseSession,
        status: 'active',
        current_round: baseRound,
      };
      expect(computeDisplayStep(activeSession)).toBe('question');
    });

    it('resolves reveal when round status is revealed', () => {
      const revealedSession: SessionModel = {
        ...baseSession,
        status: 'active',
        current_round: { ...baseRound, status: 'revealed' },
      };
      expect(computeDisplayStep(revealedSession)).toBe('reveal');
    });

    it('resolves stats when session is completed', () => {
      const completedSession: SessionModel = {
        ...baseSession,
        status: 'completed',
      };
      expect(computeDisplayStep(completedSession)).toBe('stats');
    });
  });

  describe('computeStudentStep', () => {
    it('resolves wait in lobby', () => {
      expect(computeStudentStep(baseSession, false)).toBe('wait');
    });

    it('resolves play when round is open and student has not voted', () => {
      const activeSession: SessionModel = {
        ...baseSession,
        status: 'active',
        current_round: baseRound,
      };
      expect(computeStudentStep(activeSession, false)).toBe('play');
    });

    it('resolves sent when student has voted or time ran out', () => {
      const activeSession: SessionModel = {
        ...baseSession,
        status: 'active',
        current_round: baseRound,
      };
      expect(computeStudentStep(activeSession, true)).toBe('sent');
      expect(
        computeStudentStep(
          {
            ...activeSession,
            current_round: { ...baseRound, time_remaining: 0 },
          },
          false
        )
      ).toBe('sent');
    });

    it('resolves result when revealed', () => {
      const revealedSession: SessionModel = {
        ...baseSession,
        status: 'active',
        current_round: { ...baseRound, status: 'revealed' },
      };
      expect(computeStudentStep(revealedSession, true)).toBe('result');
    });

    it('resolves final when completed', () => {
      const completedSession: SessionModel = {
        ...baseSession,
        status: 'completed',
      };
      expect(computeStudentStep(completedSession, false)).toBe('final');
    });
  });

  describe('shouldAutoCloseRound', () => {
    it('detects when clock hits zero during open round', () => {
      expect(shouldAutoCloseRound({ ...baseRound, time_remaining: 0 })).toBe(true);
      expect(shouldAutoCloseRound({ ...baseRound, time_remaining: 1 })).toBe(false);
      expect(
        shouldAutoCloseRound({
          ...baseRound,
          status: 'closed',
          time_remaining: 0,
        })
      ).toBe(false);
    });
  });
});
