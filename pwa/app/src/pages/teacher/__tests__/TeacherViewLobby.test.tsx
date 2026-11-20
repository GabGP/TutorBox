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

/** The lobby step: a match was built from the bank and has not started. */
const LOBBY_SESSION = {
  id: 's_lobby',
  title: 'Pilas',
  topic: 'arithmetic',
  status: 'lobby',
  question_count: 5,
  current_round_index: 0,
  created_at: '2026-11-20T10:00:00Z',
};

function lobbyCoordinator(overrides: Record<string, unknown> = {}) {
  return {
    sid: LOBBY_SESSION.id,
    wizard: 'count',
    setWizard: vi.fn(),
    topic: 'arithmetic',
    setTopic: vi.fn(),
    count: 5,
    setCount: vi.fn(),
    topics: [],
    session: LOBBY_SESSION,
    progress: null,
    isGenerating: false,
    isGenerationPaused: false,
    stopGeneration: vi.fn(),
    resumeGeneration: vi.fn(),
    genError: null,
    history: [],
    report: null,
    bankIds: [],
    toggleBankId: vi.fn(),
    ensureBankIds: vi.fn(),
    generateIntoBank: vi.fn(),
    cancelBankGeneration: vi.fn(),
    clearGenerationResult: vi.fn(),
    advancePrimary: vi.fn(),
    cancelMatch: vi.fn(),
    backToBankPick: vi.fn(),
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

  it('Cancelar in the lobby ends the match on the server, not just on this screen', () => {
    const coordinator = lobbyCoordinator();
    vi.mocked(useTeacherCoordinator).mockReturnValue(coordinator);
    render(<TeacherView />);

    fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }));

    expect(coordinator.cancelMatch).toHaveBeenCalledTimes(1);
    expect(coordinator.resetSession).not.toHaveBeenCalled();
  });

  it('the back arrow in the lobby returns to the bank pick', () => {
    const coordinator = lobbyCoordinator();
    vi.mocked(useTeacherCoordinator).mockReturnValue(coordinator);
    render(<TeacherView />);

    const back = screen.getByRole('button', { name: 'Volver' });
    expect(back).toBeEnabled();
    fireEvent.click(back);

    expect(coordinator.backToBankPick).toHaveBeenCalledTimes(1);
    expect(coordinator.setWizard).not.toHaveBeenCalled();
  });
});
