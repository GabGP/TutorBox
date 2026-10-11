import { render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useAuth } from '../../../features/auth/useAuth';
import { presenceApi } from '../../../features/presence/presenceApi';
import { useApplianceMode } from '../../../features/mode/useApplianceMode';
import { useSessionEngine } from '../../../features/session-engine/useSessionEngine';
import { tutorApi } from '../../../features/tutor/tutorApi';
import { useStudentVoting } from '../../../features/voting/useStudentVoting';
import { StudentView } from '../StudentView';

vi.mock('../../../features/auth/useAuth', () => ({ useAuth: vi.fn() }));
vi.mock('../../../features/mode/useApplianceMode', () => ({ useApplianceMode: vi.fn() }));
vi.mock('../../../features/session-engine/useSessionEngine', () => ({ useSessionEngine: vi.fn() }));
vi.mock('../../../features/voting/useStudentVoting', () => ({ useStudentVoting: vi.fn() }));

type Role = 'student' | 'teacher';

/** Logged in as `role` (or logged out with null), with the PIN change pending or not. */
function signIn(user: { username: string; role: Role } | null, mustChangePin = false) {
  vi.mocked(useAuth).mockReturnValue({
    user,
    loading: false,
    mustChangePin,
    pendingPin: mustChangePin ? '123456' : null,
    login: vi.fn(),
    signupAndLogin: vi.fn(),
    handlePinChange: vi.fn(),
    logout: vi.fn(),
    restoreSession: vi.fn(),
  } as unknown as ReturnType<typeof useAuth>);
}

function setClassMode(mode: 'quiz' | 'tutor' | 'apps' | null) {
  vi.mocked(useApplianceMode).mockReturnValue({
    mode,
    saving: false,
    error: null,
    setMode: vi.fn(),
  } as unknown as ReturnType<typeof useApplianceMode>);
}

/** Replaces the network call with a resolved spy. */
function spyOnHeartbeat() {
  return vi.spyOn(presenceApi, 'sendHeartbeat').mockResolvedValue(undefined);
}

describe('StudentView presence heartbeat', () => {
  let sendHeartbeat: ReturnType<typeof spyOnHeartbeat>;

  beforeEach(() => {
    vi.clearAllMocks();
    sendHeartbeat = spyOnHeartbeat();
    vi.spyOn(tutorApi, 'ping').mockResolvedValue({ status: 'ok' });
    vi.mocked(useSessionEngine).mockReturnValue({
      session: null,
      error: null,
      refresh: vi.fn(),
      setSession: vi.fn(),
    } as unknown as ReturnType<typeof useSessionEngine>);
    vi.mocked(useStudentVoting).mockReturnValue({
      votes: {},
      hits: {},
      pendingVote: null,
      currentVote: null,
      castVote: vi.fn(),
      recordHit: vi.fn(),
      score: 0,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    window.history.pushState({}, '', '/');
  });

  it('beats for a student waiting in a quiz class', () => {
    signIn({ username: 'ana', role: 'student' });
    setClassMode('quiz');

    render(<StudentView />);

    expect(sendHeartbeat).toHaveBeenCalledTimes(1);
    expect(screen.getByText('Tu maestro está preparando el juego.')).toBeInTheDocument();
  });

  it('counts the student as waiting until the class mode is known', () => {
    signIn({ username: 'ana', role: 'student' });
    setClassMode(null);

    render(<StudentView />);

    expect(sendHeartbeat).toHaveBeenCalledTimes(1);
  });

  it('does not beat in tutor mode, which keeps its own ping', () => {
    signIn({ username: 'ana', role: 'student' });
    setClassMode('tutor');

    render(<StudentView />);

    expect(sendHeartbeat).not.toHaveBeenCalled();
    expect(tutorApi.ping).toHaveBeenCalled();
  });

  it('does not beat in take-home mode', () => {
    signIn({ username: 'ana', role: 'student' });
    setClassMode('apps');

    render(<StudentView />);

    expect(sendHeartbeat).not.toHaveBeenCalled();
  });

  it('does not beat when logged out', () => {
    signIn(null);
    setClassMode('quiz');

    render(<StudentView />);

    expect(sendHeartbeat).not.toHaveBeenCalled();
    expect(screen.getByText('Entra al juego')).toBeInTheDocument();
  });

  it('does not beat for a teacher', () => {
    // On the teacher portal a teacher stays put (no redirect), so the page renders the sign-in form.
    window.history.pushState({}, '', '/maestro/');
    signIn({ username: 'profe', role: 'teacher' });
    setClassMode('quiz');

    render(<StudentView />);

    expect(sendHeartbeat).not.toHaveBeenCalled();
    expect(screen.getByText('Entra al juego')).toBeInTheDocument();
  });

  it('does not beat while a forced PIN change is pending', () => {
    signIn({ username: 'ana', role: 'student' }, true);
    setClassMode('quiz');

    render(<StudentView />);

    expect(sendHeartbeat).not.toHaveBeenCalled();
    expect(screen.getByText('Elige tu PIN nuevo')).toBeInTheDocument();
  });
});
