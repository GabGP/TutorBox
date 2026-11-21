import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as httpClient from '../../../shared/api/httpClient';
import { ApiError } from '../../../shared/api/httpClient';
import { FULL_SNAPSHOT } from '../../../features/system-health/__tests__/systemHealthFixture';
import { useAuth } from '../../../features/auth/useAuth';
import { useRosterManager } from '../../../features/roster/useRosterManager';
import { useSpeechPlayback } from '../../../features/speech/useSpeechPlayback';
import { TeacherHeader } from '../TeacherHeader';
import { TeacherView } from '../TeacherView';
import { useTeacherCoordinator } from '../useTeacherCoordinator';

vi.mock('../../../features/auth/useAuth', () => ({ useAuth: vi.fn() }));
vi.mock('../useTeacherCoordinator', () => ({ useTeacherCoordinator: vi.fn() }));
vi.mock('../../../features/roster/useRosterManager', () => ({ useRosterManager: vi.fn() }));
vi.mock('../../../features/speech/useSpeechPlayback', () => ({ useSpeechPlayback: vi.fn() }));

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

const idleCoordinator = {
  sid: null,
  wizard: 'topic' as const,
  setWizard: vi.fn(),
  topic: '',
  setTopic: vi.fn(),
  count: 10,
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
  source: 'generate' as const,
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
};

describe('TeacherHeader health button', () => {
  it('is absent unless a handler is given', () => {
    render(<TeacherHeader title="Panel" subtitle="Inicio" canGoBack={false} onBack={vi.fn()} />);

    expect(screen.queryByRole('button', { name: 'Estado del Jetson' })).not.toBeInTheDocument();
  });

  it('calls its handler when pressed', () => {
    const onOpenSystemHealth = vi.fn();
    render(
      <TeacherHeader
        title="Panel"
        subtitle="Inicio"
        canGoBack={false}
        onBack={vi.fn()}
        onOpenSystemHealth={onOpenSystemHealth}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Estado del Jetson' }));

    expect(onOpenSystemHealth).toHaveBeenCalledTimes(1);
  });
});

describe('TeacherView health sheet', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuth).mockReturnValue(teacherAuth);
    vi.mocked(useTeacherCoordinator).mockReturnValue(idleCoordinator);
    vi.mocked(useRosterManager).mockReturnValue({
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
    } as unknown as ReturnType<typeof useRosterManager>);
    vi.mocked(useSpeechPlayback).mockReturnValue({
      state: 'idle',
      message: '',
      currentRound: -1,
      speak: vi.fn(),
      prefetch: vi.fn(),
      stopPlayback: vi.fn(),
    } as unknown as ReturnType<typeof useSpeechPlayback>);
    vi.spyOn(httpClient, 'requestApi').mockImplementation(async (_method, path) => {
      if (path === '/system/health') return FULL_SNAPSHOT;
      throw new ApiError('Sin conexión con Utz\'tutor', 0);
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('opens the Jetson panel in a dialog from the header, and Escape closes it', async () => {
    render(<TeacherView />);
    fireEvent.click(screen.getByRole('button', { name: 'Estado del Jetson' }));

    const dialog = await screen.findByRole('dialog', { name: 'Estado del Jetson' });
    expect(await screen.findByRole('region', { name: 'Procesador' })).toBeInTheDocument();
    expect(dialog).toContainElement(screen.getByRole('button', { name: 'Liberar memoria' }));

    fireEvent.keyDown(document.body, { key: 'Escape' });
    expect(screen.queryByRole('dialog', { name: 'Estado del Jetson' })).not.toBeInTheDocument();
  });

  it('samples only while the sheet is open', async () => {
    render(<TeacherView />);
    await screen.findByRole('button', { name: 'Estado del Jetson' });
    expect(vi.mocked(httpClient.requestApi).mock.calls.some(([, path]) => path === '/system/health')).toBe(false);

    fireEvent.click(screen.getByRole('button', { name: 'Estado del Jetson' }));
    await screen.findByRole('region', { name: 'Procesador' });

    expect(vi.mocked(httpClient.requestApi).mock.calls.some(([, path]) => path === '/system/health')).toBe(true);
  });
});
