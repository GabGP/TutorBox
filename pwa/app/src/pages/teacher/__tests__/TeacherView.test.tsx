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
      prefetch: vi.fn(),
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

  it('renders QuestionGenerationProgress when generating in lobby', () => {
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
      wizard: 'lobby',
      setWizard: vi.fn(),
      topic: 'fractions',
      setTopic: vi.fn(),
      count: 5,
      setCount: vi.fn(),
      topics: [{ name: 'fractions', subconcepts: [] }],
      session: null,
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
      isGenerating: true,
      genError: null,
      history: [],
      report: null,
      advancePrimary: vi.fn(),
      resetSession: vi.fn(),
    });

    render(<TeacherView />);
    expect(
      screen.getByText('Creando las preguntas con IA...')
    ).toBeInTheDocument();
    expect(screen.getByText('⚡ P2')).toBeInTheDocument();

    const primaryBtn = screen.getByRole('button', { name: /Creando preguntas/ });
    expect(primaryBtn).toBeDisabled();
    expect(primaryBtn.className).not.toContain('ok');
  });

  it('triggers speech prefetching when round enters closed status', () => {
    const mockPrefetch = vi.fn();
    vi.mocked(useSpeechPlayback).mockReturnValue({
      state: 'idle',
      message: '',
      currentRound: -1,
      speak: vi.fn(),
      prefetch: mockPrefetch,
      stopPlayback: vi.fn(),
    });
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
      sid: 's1',
      wizard: 'topic',
      setWizard: vi.fn(),
      topic: 'math',
      setTopic: vi.fn(),
      count: 10,
      setCount: vi.fn(),
      topics: [],
      session: {
        id: 's1',
        title: 'Math',
        topic: 'math',
        question_count: 5,
        current_round_index: 0,
        status: 'active',
        created_at: '',
        current_round: {
          round_id: 'r1',
          round_index: 0,
          status: 'closed',
          duration_seconds: 20,
          time_remaining: 0,
          votes_cast: 5,
          question: {
            id: 'q1',
            question_text: '¿1+1?',
            options: { A: '2', B: '3' },
          },
        },
      },
      progress: null,
      isGenerating: false,
      genError: null,
      history: [],
      report: null,
      advancePrimary: vi.fn(),
      resetSession: vi.fn(),
    });

    render(<TeacherView />);
    expect(mockPrefetch).toHaveBeenCalledWith(0);
  });
});
