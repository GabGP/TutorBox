import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useAuth } from '../../../features/auth/useAuth';
import { useApplianceMode } from '../../../features/mode/useApplianceMode';
import { useSessionEngine } from '../../../features/session-engine/useSessionEngine';
import { tutorApi } from '../../../features/tutor/tutorApi';
import { useStudentVoting } from '../../../features/voting/useStudentVoting';
import { StudentView } from '../StudentView';

vi.mock('../../../features/auth/useAuth', () => ({ useAuth: vi.fn() }));
vi.mock('../../../features/mode/useApplianceMode', () => ({ useApplianceMode: vi.fn() }));
vi.mock('../../../features/session-engine/useSessionEngine', () => ({ useSessionEngine: vi.fn() }));
vi.mock('../../../features/voting/useStudentVoting', () => ({ useStudentVoting: vi.fn() }));

const auth = (user: { username: string; role: string } | null) =>
  vi.mocked(useAuth).mockReturnValue({
    user,
    loading: false,
    mustChangePin: false,
    pendingPin: null,
    login: vi.fn(),
    signupAndLogin: vi.fn(),
    handlePinChange: vi.fn(),
    logout: vi.fn(),
    restoreSession: vi.fn(),
  } as unknown as ReturnType<typeof useAuth>);

describe('StudentView in tutor mode', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(tutorApi, 'ping').mockResolvedValue({ status: 'ok' });
    vi.mocked(useApplianceMode).mockReturnValue({
      mode: 'tutor',
      saving: false,
      error: null,
      setMode: vi.fn(),
    } as unknown as ReturnType<typeof useApplianceMode>);
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

  it('asks the student to log in to use the tutor', () => {
    auth(null);
    render(<StudentView />);

    expect(screen.getByText('Entra al tutor')).toBeInTheDocument();
  });

  it('opens the chat for a logged-in student', () => {
    auth({ username: 'ana', role: 'student' });
    render(<StudentView />);

    expect(screen.getByRole('region', { name: 'Tutor de matemáticas' })).toBeInTheDocument();
    expect(screen.getByRole('status', { name: 'Conectado al tutor' })).toBeInTheDocument();
  });
});
