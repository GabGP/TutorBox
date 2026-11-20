import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useAuth } from '../../../features/auth/useAuth';
import { installFakeFleet } from '../../../features/clickers/__tests__/clickerFixture';
import { MIXED_CLASS } from '../../../features/presence/__tests__/presenceFixture';
import { presenceApi } from '../../../features/presence/presenceApi';
import { useRosterManager } from '../../../features/roster/useRosterManager';
import { useSpeechPlayback } from '../../../features/speech/useSpeechPlayback';
import { useApplianceMode } from '../../../features/mode/useApplianceMode';
import { TeacherView } from '../TeacherView';
import { useTeacherCoordinator } from '../useTeacherCoordinator';

vi.mock('../../../features/auth/useAuth', () => ({ useAuth: vi.fn() }));
vi.mock('../useTeacherCoordinator', () => ({ useTeacherCoordinator: vi.fn() }));
vi.mock('../../../features/roster/useRosterManager', () => ({ useRosterManager: vi.fn() }));
vi.mock('../../../features/speech/useSpeechPlayback', () => ({ useSpeechPlayback: vi.fn() }));
vi.mock('../../../features/mode/useApplianceMode', () => ({ useApplianceMode: vi.fn() }));

const teacherAuth = {
  user: { id: 't1', username: 'profe', role: 'teacher' as const },
  loading: false,
  mustChangePin: false,
  pendingPin: null,
  login: vi.fn(),
  signupAndLogin: vi.fn(),
  handlePinChange: vi.fn(),
  logout: vi.fn(),
  restoreSession: vi.fn(),
};

/** The lobby step: the wizard reached it and no match is running yet. */
function lobbyCoordinator(overrides: Record<string, unknown> = {}) {
  return {
    sid: null,
    wizard: 'lobby',
    setWizard: vi.fn(),
    topic: 'arithmetic',
    setTopic: vi.fn(),
    count: 5,
    setCount: vi.fn(),
    topics: [],
    session: null,
    progress: null,
    isGenerating: false,
    isGenerationPaused: false,
    stopGeneration: vi.fn(),
    resumeGeneration: vi.fn(),
    genError: null,
    history: [],
    report: null,
    source: 'generate',
    setSource: vi.fn(),
    bankIds: [],
    toggleBankId: vi.fn(),
    ensureBankIds: vi.fn(),
    pregenerate: vi.fn(),
    cancelPregeneration: vi.fn(),
    advancePrimary: vi.fn(),
    resetSession: vi.fn(),
    ...overrides,
  } as unknown as ReturnType<typeof useTeacherCoordinator>;
}

const idleRoster = {
  students: [],
  users: [],
  deleted: [],
  showDeleted: false,
  loading: false,
  pinNotice: null,
  toasts: [],
  pushToast: vi.fn(),
  dismissToast: vi.fn(),
  loadStudents: vi.fn(),
  loadUsers: vi.fn(),
  loadDeleted: vi.fn(),
  refresh: vi.fn(),
  addStudent: vi.fn(),
  resetStudentPin: vi.fn(),
  deleteStudent: vi.fn(),
  changeUserRole: vi.fn(),
  recoverStudent: vi.fn(),
  toggleDeleted: vi.fn(),
  clearPinNotice: vi.fn(),
} as unknown as ReturnType<typeof useRosterManager>;

describe('TeacherView lobby', () => {
  beforeEach(() => {
    // On the teacher portal the console stays put instead of redirecting (jsdom cannot navigate).
    window.history.pushState({}, '', '/maestro/');
    vi.mocked(useAuth).mockReturnValue(teacherAuth as unknown as ReturnType<typeof useAuth>);
    vi.mocked(useTeacherCoordinator).mockReturnValue(lobbyCoordinator());
    vi.mocked(useRosterManager).mockReturnValue(idleRoster);
    vi.mocked(useSpeechPlayback).mockReturnValue({
      state: 'idle',
      message: '',
      currentRound: -1,
      speak: vi.fn(),
      prefetch: vi.fn(),
      stopPlayback: vi.fn(),
    } as unknown as ReturnType<typeof useSpeechPlayback>);
    vi.mocked(useApplianceMode).mockReturnValue({
      mode: 'quiz',
      saving: false,
      error: null,
      setMode: vi.fn(),
    } as unknown as ReturnType<typeof useApplianceMode>);
    vi.spyOn(presenceApi, 'getClassPresence').mockResolvedValue(MIXED_CLASS);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    window.history.pushState({}, '', '/');
  });

  it('shows the class list in the lobby while the questions are still being written', async () => {
    vi.mocked(useTeacherCoordinator).mockReturnValue(
      lobbyCoordinator({
        isGenerating: true,
        progress: {
          done: 1,
          total: 5,
          failed: 0,
          ids: ['q1'],
          eta: 10,
          currentIndex: 2,
          currentTopic: 'fractions',
          currentSubconcept: null,
        },
      })
    );
    render(<TeacherView />);

    expect(screen.getByRole('heading', { name: 'Alumnos' })).toBeInTheDocument();
    expect(await screen.findByText('ana')).toBeInTheDocument();
    expect(screen.queryByText('Usuarios registrados')).not.toBeInTheDocument();
  });

  it('opens the settings sheet on the Usuarios row from Administrar usuarios', async () => {
    render(<TeacherView />);
    await screen.findByText('ana');

    fireEvent.click(screen.getByRole('button', { name: 'Administrar usuarios' }));

    const dialog = await screen.findByRole('dialog', { name: 'Ajustes' });
    expect(dialog).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Usuarios' })).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText('Usuarios registrados')).toBeInTheDocument();
  });

  it('opens settings from the gear button with no row open', async () => {
    render(<TeacherView />);
    await screen.findByText('ana');

    fireEvent.click(screen.getByRole('button', { name: 'Ajustes' }));

    await screen.findByRole('dialog', { name: 'Ajustes' });
    expect(screen.getByRole('button', { name: 'Usuarios' })).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByText('Usuarios registrados')).not.toBeInTheDocument();
  });

  it('opens the clicker sheet from Asignar clickers', async () => {
    installFakeFleet();
    render(<TeacherView />);
    await screen.findByText('ESP32-C3D002');

    fireEvent.click(screen.getByRole('button', { name: 'Asignar clickers' }));

    expect(await screen.findByRole('dialog', { name: 'Clickers' })).toBeInTheDocument();
    expect(screen.queryByRole('dialog', { name: 'Ajustes' })).not.toBeInTheDocument();
  });

  it('offers Detener while the questions are being created', () => {
    const coordinator = lobbyCoordinator({
      isGenerating: true,
      progress: { done: 1, total: 5, failed: 0, ids: ['q1'], eta: 10, currentIndex: 2 },
    });
    vi.mocked(useTeacherCoordinator).mockReturnValue(coordinator);
    render(<TeacherView />);

    fireEvent.click(screen.getByRole('button', { name: 'Detener' }));

    expect(coordinator.stopGeneration).toHaveBeenCalledTimes(1);
    expect(coordinator.resetSession).not.toHaveBeenCalled();
    expect(screen.queryByRole('button', { name: 'Cancelar' })).not.toBeInTheDocument();
  });

  it('offers Reanudar and Cancelar once creation is stopped', () => {
    const coordinator = lobbyCoordinator({
      isGenerating: true,
      isGenerationPaused: true,
      progress: { done: 1, total: 5, failed: 0, ids: ['q1'], eta: 10, currentIndex: 2 },
    });
    vi.mocked(useTeacherCoordinator).mockReturnValue(coordinator);
    render(<TeacherView />);

    expect(screen.getByRole('heading', { name: 'Creación detenida' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Reanudar' }));
    expect(coordinator.resumeGeneration).toHaveBeenCalledTimes(1);
    expect(coordinator.advancePrimary).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }));
    expect(coordinator.resetSession).toHaveBeenCalledTimes(1);
  });

  it('keeps Reanudar enabled while the creating action is still pending', () => {
    const neverSettles = new Promise<void>(() => undefined);
    const counting = lobbyCoordinator({
      wizard: 'count',
      advancePrimary: vi.fn(() => neverSettles),
    });
    vi.mocked(useTeacherCoordinator).mockReturnValue(counting);
    const { rerender } = render(<TeacherView />);
    fireEvent.click(screen.getByRole('button', { name: 'Crear las preguntas' }));

    const stopped = lobbyCoordinator({
      isGenerating: true,
      isGenerationPaused: true,
      progress: { done: 1, total: 5, failed: 0, ids: ['q1'], eta: 10, currentIndex: 2 },
    });
    vi.mocked(useTeacherCoordinator).mockReturnValue(stopped);
    rerender(<TeacherView />);

    const resume = screen.getByRole('button', { name: 'Reanudar' });
    expect(resume).toBeEnabled();
    fireEvent.click(resume);
    expect(stopped.resumeGeneration).toHaveBeenCalledTimes(1);
  });
});
