import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useAuth } from '../../../features/auth/useAuth';
import { useRosterManager } from '../../../features/roster/useRosterManager';
import { useSpeechPlayback } from '../../../features/speech/useSpeechPlayback';
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

describe('TeacherView Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        json: () => Promise.resolve({ status: 'ok' }),
      })
    );
    vi.mocked(useRosterManager).mockReturnValue({
      students: [],
      loading: false,
      error: null,
      pinNotice: null,
      loadStudents: vi.fn(),
      addStudent: vi.fn(),
      resetStudentPin: vi.fn(),
      clearError: vi.fn(),
      clearPinNotice: vi.fn(),
    });
    vi.mocked(useSpeechPlayback).mockReturnValue({
      state: 'idle',
      message: '',
      currentRound: -1,
      speak: vi.fn(),
      stopPlayback: vi.fn(),
    });
  });

  it('renders login form when teacher is unauthenticated', () => {
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
    vi.mocked(useTeacherCoordinator).mockReturnValue({
      sid: null,
      wizard: 'topic',
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
      advancePrimary: vi.fn(),
      resetSession: vi.fn(),
    });

    render(<TeacherView />);
    expect(screen.getByText('Panel del docente')).toBeInTheDocument();
  });

  it('renders topic selector on step 1 and toggles language voice', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: 't1', username: 'profe', role: 'teacher' },
      loading: false,
      mustChangePin: false,
      pendingPin: null,
      login: vi.fn(),
      signupAndLogin: vi.fn(),
      handlePinChange: vi.fn(),
      logout: vi.fn(),
      restoreSession: vi.fn(),
    });
    vi.mocked(useTeacherCoordinator).mockReturnValue({
      sid: null,
      wizard: 'topic',
      setWizard: vi.fn(),
      topic: '',
      setTopic: vi.fn(),
      count: 10,
      setCount: vi.fn(),
      topics: [{ name: 'arithmetic', subconcepts: [] }],
      session: null,
      progress: null,
      isGenerating: false,
      genError: null,
      history: [],
      report: null,
      advancePrimary: vi.fn(),
      resetSession: vi.fn(),
    });

    render(<TeacherView />);
    expect(screen.getByText('Elegir tema')).toBeInTheDocument();
    expect(screen.getByText('Aritmética')).toBeInTheDocument();

    const voiceBtn = screen.getByRole('button', { name: 'Voz ES' });
    fireEvent.click(voiceBtn);
    expect(screen.getByRole('button', { name: "Voz K'iche'" })).toBeInTheDocument();
  });
});
