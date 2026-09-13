import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useSessionEngine } from '../../../features/session-engine/useSessionEngine';
import { DisplayView } from '../DisplayView';

vi.mock('../../../features/session-engine/useSessionEngine', () => ({
  useSessionEngine: vi.fn(),
}));

describe('DisplayView Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders idle screen when there is no active session', () => {
    vi.mocked(useSessionEngine).mockReturnValue({
      session: null,
      error: null,
      refresh: vi.fn(),
      setSession: vi.fn(),
    });

    render(<DisplayView />);
    expect(screen.getByText('TutorBox está listo')).toBeInTheDocument();
    expect(
      screen.getByText('Esperando a que el docente inicie el juego')
    ).toBeInTheDocument();
  });

  it('renders question screen when session round is active', () => {
    vi.mocked(useSessionEngine).mockReturnValue({
      session: {
        id: 's1',
        title: 'Class Game',
        topic: 'arithmetic',
        status: 'active',
        question_count: 5,
        current_round_index: 0,
        created_at: new Date().toISOString(),
        current_round: {
          round_id: 'r1',
          round_index: 0,
          duration_seconds: 20,
          time_remaining: 15,
          status: 'open',
          votes_cast: 4,
          question: {
            id: 'q1',
            question_text: '¿Cuánto es 7 * 8?',
            options: { A: '56', B: '54', C: '48', D: '64' },
          },
        },
      },
      error: null,
      refresh: vi.fn(),
      setSession: vi.fn(),
    });

    render(<DisplayView />);
    expect(screen.getByText('¿Cuánto es 7 * 8?')).toBeInTheDocument();
    expect(screen.getByText(/Pregunta 1 de 5 · 4 respuestas/)).toBeInTheDocument();
    expect(screen.getByText('56')).toBeInTheDocument();
  });
});
