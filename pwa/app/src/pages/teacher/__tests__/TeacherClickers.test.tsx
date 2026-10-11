import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { installFakeFleet } from '../../../features/clickers/__tests__/clickerFixture';
import { useAuth } from '../../../features/auth/useAuth';
import { useRosterManager } from '../../../features/roster/useRosterManager';
import { useSpeechPlayback } from '../../../features/speech/useSpeechPlayback';
import { TeacherHeader } from '../TeacherHeader';
import { TeacherView } from '../TeacherView';
import { useTeacherCoordinator } from '../useTeacherCoordinator';

vi.mock('../../../features/auth/useAuth', () => ({
  useAuth: vi.fn(),
}));

vi.mock('../useTeacherCoordinator', () => ({
  useTeacherCoordinator: vi.fn(),
}));

vi.mock('../../../features/roster/useRosterManager', () => ({
  useRosterManager: vi.fn(),
}));

vi.mock('../../../features/speech/useSpeechPlayback', () => ({
  useSpeechPlayback: vi.fn(),
}));

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
  genError: null,
  history: [],
  report: null,
  source: 'generate' as const,
  setSource: vi.fn(),
  bankIds: [],
  toggleBankId: vi.fn(),
  ensureBankIds: vi.fn(),
  pregenerate: vi.fn(),
  advancePrimary: vi.fn(),
  resetSession: vi.fn(),
};

describe('TeacherHeader Clickers button', () => {
  it('is absent unless a handler is given', () => {
    render(
      <TeacherHeader
        title="Panel"
        subtitle="Inicio"
        step="topic"
        voiceLang="es"
        onBack={vi.fn()}
        onToggleVoice={vi.fn()}
      />
    );
    expect(screen.queryByRole('button', { name: 'Clickers' })).not.toBeInTheDocument();
  });

  it('calls the handler and sits before the settings button', () => {
    const onOpenClickers = vi.fn();
    render(
      <TeacherHeader
        title="Panel"
        subtitle="Inicio"
        step="topic"
        voiceLang="es"
        onBack={vi.fn()}
        onToggleVoice={vi.fn()}
        onOpenSettings={vi.fn()}
        onOpenClickers={onOpenClickers}
      />
    );
    const names = screen.getAllByRole('button').map((button) => button.getAttribute('aria-label') ?? button.textContent);
    expect(names.indexOf('Clickers')).toBe(names.indexOf('Ajustes') - 1);
    fireEvent.click(screen.getByRole('button', { name: 'Clickers' }));
    expect(onOpenClickers).toHaveBeenCalledTimes(1);
  });
});

describe('TeacherView Clickers sheet', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

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
    });
    vi.mocked(useSpeechPlayback).mockReturnValue({
      state: 'idle',
      message: '',
      currentRound: -1,
      speak: vi.fn(),
      prefetch: vi.fn(),
      stopPlayback: vi.fn(),
    });
  });

  it('opens the fleet in a dialog labelled Clickers', async () => {
    installFakeFleet();
    render(<TeacherView />);
    fireEvent.click(screen.getByRole('button', { name: 'Clickers' }));
    const dialog = await screen.findByRole('dialog', { name: 'Clickers' });
    expect(await screen.findByRole('button', { name: 'ESP32-A4CF12' })).toBeInTheDocument();
    expect(dialog).toContainElement(screen.getByRole('button', { name: 'ESP32-A4CF12' }));
    expect(screen.queryByRole('dialog', { name: 'Ajustes' })).not.toBeInTheDocument();
  });

  it('closes on Escape', async () => {
    installFakeFleet();
    render(<TeacherView />);
    fireEvent.click(screen.getByRole('button', { name: 'Clickers' }));
    await screen.findByRole('dialog', { name: 'Clickers' });
    fireEvent.keyDown(document.body, { key: 'Escape' });
    expect(screen.queryByRole('dialog', { name: 'Clickers' })).not.toBeInTheDocument();
  });

  it('closes when the teacher logs out', async () => {
    installFakeFleet();
    const { rerender } = render(<TeacherView />);
    fireEvent.click(screen.getByRole('button', { name: 'Clickers' }));
    await screen.findByRole('dialog', { name: 'Clickers' });

    vi.mocked(useAuth).mockReturnValue({ ...teacherAuth, user: null });
    rerender(<TeacherView />);
    vi.mocked(useAuth).mockReturnValue(teacherAuth);
    rerender(<TeacherView />);
    expect(screen.queryByRole('dialog', { name: 'Clickers' })).not.toBeInTheDocument();
  });
});
