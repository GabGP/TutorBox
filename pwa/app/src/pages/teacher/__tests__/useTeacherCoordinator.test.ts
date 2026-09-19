import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { SessionModel } from '../../../features/session-engine/session.types';
import { sessionApi } from '../../../features/session-engine/sessionApi';
import { useTeacherCoordinator } from '../useTeacherCoordinator';

vi.mock('../../../features/session-engine/sessionApi', () => ({
  sessionApi: {
    getCurrentSession: vi.fn(),
    getSessionById: vi.fn(),
    createSession: vi.fn(),
    startSession: vi.fn(),
    closeRound: vi.fn(),
    revealRound: vi.fn(),
    nextRound: vi.fn(),
    getSessionReport: vi.fn(),
  },
}));

vi.mock('../../../features/speech/useTTSLifecycle', () => ({
  useTTSLifecycle: () => ({
    preloadIfUnloaded: vi.fn().mockResolvedValue(undefined),
    unloadIfLoaded: vi.fn().mockResolvedValue(undefined),
  }),
}));

vi.mock('../../../shared/lib/sound', () => ({
  unlockAudio: vi.fn(),
}));

describe('useTeacherCoordinator Hook', () => {
  const baseSession: SessionModel = {
    id: 's_test1',
    title: 'Test Match',
    topic: 'arithmetic',
    status: 'active',
    question_count: 3,
    current_round_index: 0,
    created_at: new Date().toISOString(),
    current_round: {
      round_id: 'r_0',
      round_index: 0,
      status: 'open',
      duration_seconds: 20,
      time_remaining: 15,
      votes_cast: 4,
      question: {
        id: 'q_1',
        question_text: '¿2 + 2?',
        options: { A: '4', B: '5', C: '3', D: '22' },
      },
    },
  };

  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('closes active round when advancePrimary is invoked during open status', async () => {
    vi.mocked(sessionApi.getSessionById).mockResolvedValue(baseSession);
    const closedSession: SessionModel = {
      ...baseSession,
      current_round: {
        ...baseSession.current_round!,
        status: 'closed',
      },
    };
    vi.mocked(sessionApi.closeRound).mockResolvedValue(closedSession);

    const { result } = renderHook(() => useTeacherCoordinator('s_test1'));

    await act(async () => {
      // allow initial poll to populate session
      await Promise.resolve();
    });

    expect(result.current.session?.current_round?.status).toBe('open');

    await act(async () => {
      await result.current.advancePrimary();
    });

    expect(sessionApi.closeRound).toHaveBeenCalledWith('s_test1');
    expect(sessionApi.revealRound).not.toHaveBeenCalled();
    expect(result.current.session?.current_round?.status).toBe('closed');
  });

  it('reveals round when advancePrimary is invoked during closed status', async () => {
    const closedSession: SessionModel = {
      ...baseSession,
      current_round: {
        ...baseSession.current_round!,
        status: 'closed',
      },
    };
    const revealedSession: SessionModel = {
      ...baseSession,
      current_round: {
        ...baseSession.current_round!,
        status: 'revealed',
        result: {
          tally: {
            counts: { A: 1, B: 3, C: 0, D: 0 },
            total_votes: 4,
            correct_option: 'A',
            correct_count: 1,
            correct_percentage: 25,
          },
          decision: {
            should_speak: true,
            dominant_distractor: 'B',
            dominant_percentage: 75,
            explanation: 'Recuerda sumar unidades primero.',
          },
          explanations: { B: 'Recuerda sumar unidades primero.' },
        },
      },
    };

    vi.mocked(sessionApi.getSessionById)
      .mockResolvedValueOnce(closedSession)
      .mockResolvedValueOnce(revealedSession);
    vi.mocked(sessionApi.revealRound).mockResolvedValue(undefined);

    const { result } = renderHook(() => useTeacherCoordinator('s_test1'));

    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current.session?.current_round?.status).toBe('closed');

    await act(async () => {
      await result.current.advancePrimary();
    });

    expect(sessionApi.revealRound).toHaveBeenCalledWith('s_test1');
    expect(sessionApi.closeRound).not.toHaveBeenCalled();
    expect(result.current.session?.current_round?.status).toBe('revealed');
  });

  it('advances to next round when advancePrimary is invoked during revealed status', async () => {
    const revealedSession: SessionModel = {
      ...baseSession,
      current_round: {
        ...baseSession.current_round!,
        status: 'revealed',
      },
    };
    const nextSession: SessionModel = {
      ...baseSession,
      current_round_index: 1,
      current_round: {
        round_id: 'r_1',
        round_index: 1,
        status: 'open',
        duration_seconds: 20,
        time_remaining: 20,
        votes_cast: 0,
        question: {
          id: 'q_2',
          question_text: '¿5 * 2?',
          options: { A: '10', B: '7', C: '25', D: '52' },
        },
      },
    };

    vi.mocked(sessionApi.getSessionById).mockResolvedValue(revealedSession);
    vi.mocked(sessionApi.nextRound).mockResolvedValue(nextSession);

    const { result } = renderHook(() => useTeacherCoordinator('s_test1'));

    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current.session?.current_round?.status).toBe('revealed');

    await act(async () => {
      await result.current.advancePrimary();
    });

    expect(sessionApi.nextRound).toHaveBeenCalledWith('s_test1');
    expect(result.current.session?.current_round_index).toBe(1);
    expect(result.current.session?.current_round?.status).toBe('open');
  });

  it('automatically closes open round when time_remaining reaches 0', async () => {
    const expiredSession: SessionModel = {
      ...baseSession,
      current_round: {
        ...baseSession.current_round!,
        time_remaining: 0,
      },
    };
    const closedSession: SessionModel = {
      ...expiredSession,
      current_round: {
        ...expiredSession.current_round!,
        status: 'closed',
      },
    };

    vi.mocked(sessionApi.getSessionById).mockResolvedValue(expiredSession);
    vi.mocked(sessionApi.closeRound).mockResolvedValue(closedSession);

    renderHook(() => useTeacherCoordinator('s_test1'));

    await act(async () => {
      await Promise.resolve();
    });

    expect(sessionApi.closeRound).toHaveBeenCalledWith('s_test1');
  });
});
