import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { EMPTY_CLASS, MIXED_CLASS } from '../../../features/presence/__tests__/presenceFixture';
import { presenceApi } from '../../../features/presence/presenceApi';
import { TeacherLobby } from '../TeacherLobby';

const lobbyHandlers = () => ({
  onManageUsers: vi.fn(),
  onOpenClickers: vi.fn(),
});

describe('TeacherLobby Component', () => {
  beforeEach(() => {
    vi.spyOn(presenceApi, 'getClassPresence').mockResolvedValue(EMPTY_CLASS);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders QuestionGenerationProgress when generating questions without active session', async () => {
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
        hostAddress="192.168.4.1/alumno"
        {...lobbyHandlers()}
      />
    );

    expect(
      screen.getByText('Creando las preguntas con IA...')
    ).toBeInTheDocument();
    expect(screen.getByText('192.168.4.1/alumno')).toBeInTheDocument();
    // The class list shows while the questions are still being written.
    expect(screen.getByRole('heading', { name: 'Alumnos' })).toBeInTheDocument();
    expect(await screen.findByText(/Todavía no hay alumnos/)).toBeInTheDocument();
  });

  it('renders ready hero when session exists', async () => {
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
        hostAddress="192.168.4.1/alumno"
        {...lobbyHandlers()}
      />
    );

    expect(screen.getByText('PREGUNTAS LISTAS')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('192.168.4.1/alumno')).toBeInTheDocument();
    await screen.findByText(/Todavía no hay alumnos/);
  });

  it('surfaces partial failures inside the progress card instead of a separate note', async () => {
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
        hostAddress="192.168.4.1/alumno"
        {...lobbyHandlers()}
      />
    );

    // Failure state lives in the card (pills + badge + caption)…
    expect(
      screen.getByText(/1 pregunta\(s\) con error/)
    ).toBeInTheDocument();
    expect(
      screen.getByText('2 de 3 preguntas listas. 1 no salieron del modelo.')
    ).toBeInTheDocument();
    // …not in the old duplicated note below the card.
    expect(screen.queryByText(/no salieron del modelo; el juego tendrá/)).toBeNull();
    await screen.findByText(/Todavía no hay alumnos/);
  });

  it('no longer renders the user table; the class list replaces it', async () => {
    render(
      <TeacherLobby
        session={null}
        progress={null}
        hostAddress="192.168.4.1/alumno"
        {...lobbyHandlers()}
      />
    );

    expect(screen.queryByText('Usuarios registrados')).not.toBeInTheDocument();
    expect(await screen.findByText(/Todavía no hay alumnos/)).toBeInTheDocument();
  });

  it('shows who is connected and hands Administrar usuarios to its handler', async () => {
    vi.mocked(presenceApi.getClassPresence).mockResolvedValue(MIXED_CLASS);
    const handlers = lobbyHandlers();
    render(
      <TeacherLobby session={null} progress={null} hostAddress="192.168.4.1/alumno" {...handlers} />
    );

    expect(await screen.findByText('ana')).toBeInTheDocument();
    expect(screen.getByText('1 de 3 conectados · 1 se cayó')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Administrar usuarios' }));
    expect(handlers.onManageUsers).toHaveBeenCalledTimes(1);
  });

  it('sends the teacher to the clickers from the unassigned note', async () => {
    vi.mocked(presenceApi.getClassPresence).mockResolvedValue(MIXED_CLASS);
    const handlers = lobbyHandlers();
    render(
      <TeacherLobby session={null} progress={null} hostAddress="192.168.4.1/alumno" {...handlers} />
    );

    expect(await screen.findByText('ESP32-C3D002')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Asignar clickers' }));
    expect(handlers.onOpenClickers).toHaveBeenCalledTimes(1);
    expect(handlers.onManageUsers).not.toHaveBeenCalled();
  });
});
