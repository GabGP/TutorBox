import { act, renderHook } from '@testing-library/react';
import { ApiError } from '../../../shared/api/httpClient';
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
    abandonSession: vi.fn(),
    getSessionReport: vi.fn(),
  },
}));

const { mockPreloadIfUnloaded, mockUnloadIfLoaded, mockTtsStatus, mockTtsUnload } =
  vi.hoisted(() => ({
    mockPreloadIfUnloaded: vi.fn(),
    mockUnloadIfLoaded: vi.fn(),
    mockTtsStatus: vi.fn(),
    mockTtsUnload: vi.fn(),
  }));

vi.mock('../../../features/speech/useTTSLifecycle', () => ({
  useTTSLifecycle: () => ({
    preloadIfUnloaded: mockPreloadIfUnloaded,
    unloadIfLoaded: mockUnloadIfLoaded,
  }),
}));

vi.mock('../../../features/speech/speechApi', () => ({
  ttsApi: {
    getStatus: (...args: unknown[]) => mockTtsStatus(...args),
    unload: (...args: unknown[]) => mockTtsUnload(...args),
    load: vi.fn(),
    getVoices: vi.fn(),
  },
  speechApi: {
    getSpeechBlobUrl: vi.fn(),
    getPreviewBlobUrl: vi.fn(),
  },
}));

vi.mock('../../../shared/lib/sound', () => ({
  unlockAudio: vi.fn(),
}));

describe('useTeacherCoordinator cancelMatch', () => {
  const activeSession: SessionModel = {
    id: 's_live',
    title: 'Partida',
    topic: 'arithmetic',
    status: 'active',
    question_count: 3,
    current_round_index: 1,
    created_at: new Date().toISOString(),
  };

  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    // A finished match loads its report; it never needs to arrive here.
    vi.mocked(sessionApi.getSessionReport).mockReturnValue(new Promise(() => undefined));
  });

  async function renderWith(session: SessionModel) {
    vi.mocked(sessionApi.getSessionById).mockResolvedValue(session);
    const hook = renderHook(() => useTeacherCoordinator(session.id));
    await act(async () => {
      await Promise.resolve();
    });
    expect(hook.result.current.session?.id).toBe(session.id);
    return hook;
  }

  it('ends a started match on the server, then starts the console over', async () => {
    vi.mocked(sessionApi.abandonSession).mockResolvedValue({ ...activeSession, status: 'abandoned' });
    const { result } = await renderWith(activeSession);

    await act(async () => {
      await result.current.cancelMatch();
    });

    expect(sessionApi.abandonSession).toHaveBeenCalledWith('s_live');
    expect(result.current.session).toBeNull();
    expect(result.current.sid).toBeNull();
    expect(result.current.wizard).toBe('topic');
  });

  it('ends a lobby on the server too, so students stop seeing it', async () => {
    vi.mocked(sessionApi.abandonSession).mockResolvedValue({ ...activeSession, status: 'abandoned' });
    const { result } = await renderWith({ ...activeSession, status: 'lobby' });

    await act(async () => {
      await result.current.cancelMatch();
    });

    expect(sessionApi.abandonSession).toHaveBeenCalledWith('s_live');
    expect(result.current.session).toBeNull();
  });

  it('still resets when the server already ended the match', async () => {
    vi.mocked(sessionApi.abandonSession).mockRejectedValue(new ApiError('Ya terminó', 409));
    const { result } = await renderWith(activeSession);

    await act(async () => {
      await result.current.cancelMatch();
    });

    expect(result.current.session).toBeNull();
  });

  it('does not call the server for a finished match', async () => {
    const { result } = await renderWith({ ...activeSession, status: 'completed' });

    await act(async () => {
      await result.current.cancelMatch();
    });

    expect(sessionApi.abandonSession).not.toHaveBeenCalled();
    expect(result.current.session).toBeNull();
  });
});
