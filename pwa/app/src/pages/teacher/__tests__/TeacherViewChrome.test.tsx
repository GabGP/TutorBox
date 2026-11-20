import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useAuth } from '../../../features/auth/useAuth';
import { useApplianceMode } from '../../../features/mode/useApplianceMode';
import { useRosterManager } from '../../../features/roster/useRosterManager';
import { useSpeechPlayback } from '../../../features/speech/useSpeechPlayback';
import { tutorApi } from '../../../features/tutor/tutorApi';
import { TeacherView } from '../TeacherView';
import { useTeacherCoordinator } from '../useTeacherCoordinator';

vi.mock('../../../features/auth/useAuth', () => ({ useAuth: vi.fn() }));
vi.mock('../useTeacherCoordinator', () => ({ useTeacherCoordinator: vi.fn() }));
vi.mock('../../../features/roster/useRosterManager', () => ({ useRosterManager: vi.fn() }));
vi.mock('../../../features/speech/useSpeechPlayback', () => ({ useSpeechPlayback: vi.fn() }));
vi.mock('../../../features/mode/useApplianceMode', () => ({ useApplianceMode: vi.fn() }));

const logout = vi.fn();
const pushToast = vi.fn();

/** Step 1 of the quiz: no match yet, the wizard on the topic list. */
const topicCoordinator = {
  sid: null,
  wizard: 'topic',
  setWizard: vi.fn(),
  topic: '',
  setTopic: vi.fn(),
  count: 5,
  setCount: vi.fn(),
  topics: [{ name: 'arithmetic', subconcepts: [] }],
  session: null,
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
  resetSession: vi.fn(),
} as unknown as ReturnType<typeof useTeacherCoordinator>;

function classMode(mode: 'quiz' | 'tutor' | 'apps', error: string | null = null) {
  vi.mocked(useApplianceMode).mockReturnValue({
    mode,
    saving: false,
    error,
    setMode: vi.fn(),
  } as unknown as ReturnType<typeof useApplianceMode>);
}

describe('TeacherView top bar, logout and mode errors', () => {
  beforeEach(() => {
    window.history.pushState({}, '', '/maestro/');
    vi.mocked(useAuth).mockReturnValue({
      user: { id: 't1', username: 'profe', role: 'teacher' },
      loading: false,
      mustChangePin: false,
      pendingPin: null,
      login: vi.fn(),
      signupAndLogin: vi.fn(),
      handlePinChange: vi.fn(),
      logout,
      restoreSession: vi.fn(),
    } as unknown as ReturnType<typeof useAuth>);
    vi.mocked(useTeacherCoordinator).mockReturnValue(topicCoordinator);
    vi.mocked(useRosterManager).mockReturnValue({
      users: [],
      deleted: [],
      showDeleted: false,
      pinNotice: null,
      toasts: [],
      pushToast,
      dismissToast: vi.fn(),
    } as unknown as ReturnType<typeof useRosterManager>);
    vi.mocked(useSpeechPlayback).mockReturnValue({
      state: 'idle',
      message: '',
      speak: vi.fn(),
      prefetch: vi.fn(),
      stopPlayback: vi.fn(),
    } as unknown as ReturnType<typeof useSpeechPlayback>);
    vi.spyOn(tutorApi, 'students').mockResolvedValue([]);
    classMode('quiz');
  });

  afterEach(() => {
    vi.restoreAllMocks();
    logout.mockReset();
    pushToast.mockReset();
    window.history.pushState({}, '', '/');
  });

  it('has no Salir in the footer: logging out lives in Ajustes', async () => {
    render(<TeacherView />);
    expect(screen.queryByRole('button', { name: 'Salir' })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Ajustes' }));
    await screen.findByRole('dialog', { name: 'Ajustes' });
    fireEvent.click(screen.getByRole('button', { name: 'Cerrar sesión' }));

    expect(logout).toHaveBeenCalledTimes(1);
  });

  it('titles the top bar after the class mode, without the quiz back and voice buttons', () => {
    classMode('tutor');
    const { rerender } = render(<TeacherView />);
    // The mode picker repeats these words, so read the bar itself.
    const bar = () => [document.getElementById('subtitle')?.textContent, document.getElementById('title')?.textContent];

    expect(bar()).toEqual(['Modo tutor', 'Chat de práctica']);
    expect(screen.queryByRole('button', { name: 'Volver' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Voz ES' })).not.toBeInTheDocument();

    classMode('apps');
    rerender(<TeacherView />);
    expect(bar()).toEqual(['Llevar a casa', 'App para el teléfono']);

    classMode('quiz');
    rerender(<TeacherView />);
    expect(bar()).toEqual(['Paso 1 de 3', 'Elegir tema']);
    expect(screen.getByRole('button', { name: 'Volver' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Voz ES' })).toBeInTheDocument();
  });

  it('floats a refused mode switch as an error toast instead of a line under the picker', () => {
    classMode('quiz', 'Hay un juego en curso');
    render(<TeacherView />);

    expect(pushToast).toHaveBeenCalledWith({ message: 'Hay un juego en curso', tone: 'error' });
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});
