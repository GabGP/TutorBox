import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { TeacherLobby } from '../TeacherLobby';

describe('TeacherLobby Component', () => {
  const dummyRosterProps = {
    students: [],
    error: null,
    pinNotice: null,
    onAddStudent: vi.fn(),
    onResetPin: vi.fn(),
  };

  it('renders QuestionGenerationProgress when generating questions without active session', () => {
    render(
      <TeacherLobby
        session={null}
        progress={{
          done: 1,
          total: 3,
          failed: 0,
          ids: ['q1'],
          eta: 8,
          currentIndex: 2,
          currentTopic: 'arithmetic',
        }}
        rosterProps={dummyRosterProps}
        hostAddress="192.168.4.1/alumno"
      />
    );

    expect(
      screen.getByText('Creando las preguntas con IA...')
    ).toBeInTheDocument();
    expect(screen.getByText('192.168.4.1/alumno')).toBeInTheDocument();
    expect(screen.getByText('Alumnos registrados')).toBeInTheDocument();
  });

  it('renders ready hero when session exists', () => {
    render(
      <TeacherLobby
        session={{
          id: 's-123',
          title: 'Sesión de prueba',
          topic: 'arithmetic',
          status: 'lobby',
          question_count: 5,
          current_round_index: 0,
          created_at: new Date().toISOString(),
        }}
        progress={null}
        rosterProps={dummyRosterProps}
        hostAddress="192.168.4.1/alumno"
      />
    );

    expect(screen.getByText('PREGUNTAS LISTAS')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('192.168.4.1/alumno')).toBeInTheDocument();
  });

  it('surfaces partial failures inside the progress card instead of a separate note', () => {
    render(
      <TeacherLobby
        session={{
          id: 's-123',
          title: 'Sesión',
          topic: 'arithmetic',
          status: 'lobby',
          question_count: 2,
          current_round_index: 0,
          created_at: new Date().toISOString(),
        }}
        progress={{
          done: 3,
          total: 3,
          failed: 1,
          ids: ['q1', 'q2'],
          eta: 5,
          statuses: ['success', 'failed', 'success'],
        }}
        rosterProps={dummyRosterProps}
        hostAddress="192.168.4.1/alumno"
      />
    );

    // Failure state lives in the card (pills + badge + caption)…
    expect(
      screen.getByText(/1 pregunta\(s\) con error/)
    ).toBeInTheDocument();
    expect(
      screen.getByText('✓ 2 de 3 preguntas listas. 1 no salieron del modelo.')
    ).toBeInTheDocument();
    // …not in the old duplicated note below the card.
    expect(screen.queryByText(/no salieron del modelo; el juego tendrá/)).toBeNull();
  });
});
