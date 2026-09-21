import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useAuth } from '../../../features/auth/useAuth';
import { useSessionEngine } from '../../../features/session-engine/useSessionEngine';
import { useStudentVoting } from '../../../features/voting/useStudentVoting';
import { StudentView } from '../StudentView';

vi.mock('../../../features/auth/useAuth', () => ({
  useAuth: vi.fn(),
}));

vi.mock('../../../features/session-engine/useSessionEngine', () => ({
  useSessionEngine: vi.fn(),
}));

vi.mock('../../../features/voting/useStudentVoting', () => ({
  useStudentVoting: vi.fn(),
}));

describe('StudentView Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    delete document.body.dataset.mood;

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

  it('renders login form and persistent unauthenticated header when student is not logged in', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: false,
      mustChangePin: false,
      pendingPin: null,
      login: vi.fn(),
      signupAndLogin: vi.fn(),
      handlePinChange: vi.fn(),
      logout: vi.fn(),
      restoreSession: vi.fn(),
    });
    vi.mocked(useSessionEngine).mockReturnValue({
      session: null,
      error: null,
      refresh: vi.fn(),
      setSession: vi.fn(),
    });

    render(<StudentView />);
    expect(screen.getByText('TutorBox')).toBeInTheDocument();
    expect(screen.getByText('Sin conexión')).toBeInTheDocument();
    expect(screen.queryByText('Salir')).not.toBeInTheDocument();
    expect(screen.getByText('Entra al juego')).toBeInTheDocument();
  });

  it('renders waiting screen with student identity and logout button when in lobby', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: 'u1', username: 'carlos', role: 'student' },
      loading: false,
      mustChangePin: false,
      pendingPin: null,
      login: vi.fn(),
      signupAndLogin: vi.fn(),
      handlePinChange: vi.fn(),
      logout: vi.fn(),
      restoreSession: vi.fn(),
    });
    vi.mocked(useSessionEngine).mockReturnValue({
      session: null,
      error: null,
      refresh: vi.fn(),
      setSession: vi.fn(),
    });

    render(<StudentView />);
    expect(screen.getByText('carlos')).toBeInTheDocument();
    expect(screen.getByText('Salir')).toBeInTheDocument();
    expect(screen.getByText('Hola, carlos')).toBeInTheDocument();
    expect(screen.getByText('C')).toBeInTheDocument();
    expect(screen.getByText('Tu maestro está preparando el juego.')).toBeInTheDocument();
  });

  it('opens the account sheet when tapping the username', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: 'u1', username: 'carlos', role: 'student' },
      loading: false,
      mustChangePin: false,
      pendingPin: null,
      login: vi.fn(),
      signupAndLogin: vi.fn(),
      handlePinChange: vi.fn(),
      logout: vi.fn(),
      restoreSession: vi.fn(),
    });
    vi.mocked(useSessionEngine).mockReturnValue({
      session: null,
      error: null,
      refresh: vi.fn(),
      setSession: vi.fn(),
    });

    render(<StudentView />);
    fireEvent.click(screen.getByRole('button', { name: 'carlos' }));
    expect(screen.getByText('Cambiar mi nombre')).toBeInTheDocument();
    expect(screen.getByText('Cambiar PIN')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Volver al juego' }));
    expect(screen.getByText('Hola, carlos')).toBeInTheDocument();
  });

  it('renders play screen with question and option tiles when round is open', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: 'u1', username: 'carlos', role: 'student' },
      loading: false,
      mustChangePin: false,
      pendingPin: null,
      login: vi.fn(),
      signupAndLogin: vi.fn(),
      handlePinChange: vi.fn(),
      logout: vi.fn(),
      restoreSession: vi.fn(),
    });
    vi.mocked(useSessionEngine).mockReturnValue({
      session: {
        id: 's1',
        title: 'Quiz 1',
        status: 'active',
        topic: 'arithmetic',
        question_count: 5,
        current_round_index: 0,
        created_at: '2026-09-13T10:00:00Z',
        current_round: {
          round_id: 'r1',
          round_index: 0,
          status: 'open',
          duration_seconds: 20,
          time_remaining: 15,
          votes_cast: 0,
          question: {
            id: 'q1',
            topic: 'arithmetic',
            question_text: '¿Cuánto es 4 + 4?',
            options: { A: '6', B: '8', C: '10', D: '12' },
          },
        },
      },
      error: null,
      refresh: vi.fn(),
      setSession: vi.fn(),
    });

    render(<StudentView />);
    expect(screen.getByText('Pregunta 1 de 5')).toBeInTheDocument();
    expect(screen.getByText('¿Cuánto es 4 + 4?')).toBeInTheDocument();
    expect(screen.getByText('6')).toBeInTheDocument();
    expect(screen.getByText('8')).toBeInTheDocument();
  });

  it('renders result screen and applies good mood when round is revealed and answer was correct', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: 'u1', username: 'carlos', role: 'student' },
      loading: false,
      mustChangePin: false,
      pendingPin: null,
      login: vi.fn(),
      signupAndLogin: vi.fn(),
      handlePinChange: vi.fn(),
      logout: vi.fn(),
      restoreSession: vi.fn(),
    });
    vi.mocked(useStudentVoting).mockReturnValue({
      votes: { r1: 'B' },
      hits: { r1: true },
      pendingVote: null,
      currentVote: 'B',
      castVote: vi.fn(),
      recordHit: vi.fn(),
      score: 1,
    });
    vi.mocked(useSessionEngine).mockReturnValue({
      session: {
        id: 's1',
        title: 'Quiz 1',
        status: 'active',
        topic: 'arithmetic',
        question_count: 5,
        current_round_index: 0,
        created_at: '2026-09-13T10:00:00Z',
        current_round: {
          round_id: 'r1',
          round_index: 0,
          status: 'revealed',
          duration_seconds: 20,
          time_remaining: 0,
          votes_cast: 1,
          question: {
            id: 'q1',
            topic: 'arithmetic',
            question_text: '¿Cuánto es 4 + 4?',
            options: { A: '6', B: '8', C: '10', D: '12' },
          },
          result: {
            tally: {
              counts: { A: 0, B: 1, C: 0, D: 0 },
              total_votes: 1,
              correct_option: 'B',
              correct_count: 1,
              correct_percentage: 100,
            },
            decision: {
              should_speak: false,
              dominant_distractor: '',
              dominant_percentage: 0,
              explanation: '',
            },
            explanations: { A: 'Error suma', C: 'Error suma', D: 'Error suma' },
          },
        },
      },
      error: null,
      refresh: vi.fn(),
      setSession: vi.fn(),
    });

    render(<StudentView />);
    expect(screen.getByText('¡Correcto!')).toBeInTheDocument();
    expect(screen.getByText('B · 8')).toBeInTheDocument();
    expect(screen.getByText('1 de 1 correctas')).toBeInTheDocument();
    expect(document.body.dataset.mood).toBe('good');
  });

  it('renders forced PIN rotation modal when mustChangePin is true', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: false,
      mustChangePin: true,
      pendingPin: '123456',
      login: vi.fn(),
      signupAndLogin: vi.fn(),
      handlePinChange: vi.fn(),
      logout: vi.fn(),
      restoreSession: vi.fn(),
    });
    vi.mocked(useSessionEngine).mockReturnValue({
      session: null,
      error: null,
      refresh: vi.fn(),
      setSession: vi.fn(),
    });

    render(<StudentView />);
    expect(screen.getByText('Elige tu PIN nuevo')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('PIN nuevo (4 a 8 números)')).toBeInTheDocument();
  });
});
