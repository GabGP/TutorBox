import { act, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  GenerationProgress,
} from '../generator.types';
import {
  PEDAGOGICAL_STAGES,
  PROGRESS_ANIMATION,
} from '../generator.constants';
import { formatDuration, QuestionGenerationProgress } from '../QuestionGenerationProgress';

describe('QuestionGenerationProgress Component', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  const mockProgress: GenerationProgress = {
    done: 2,
    total: 5,
    failed: 0,
    ids: ['q1', 'q2'],
    eta: 12,
    currentIndex: 3,
    currentTopic: 'fractions',
    currentSubconcept: 'addition_subtraction',
  };

  it('renders title, localized topic badges, and question counter without hardware jargon', () => {
    render(<QuestionGenerationProgress progress={mockProgress} />);

    expect(screen.getByText('Creando las preguntas con IA...')).toBeInTheDocument();
    expect(screen.queryByText('IA Local Jetson')).toBeNull();
    expect(screen.getByText('Fracciones')).toBeInTheDocument();
    expect(screen.getByText('Suma y resta')).toBeInTheDocument();
    expect(screen.getByText('Pregunta de')).toBeInTheDocument();
    expect(screen.getByText('40%')).toBeInTheDocument();
  });

  it('renders step pills with done, active, and pending states', () => {
    render(<QuestionGenerationProgress progress={mockProgress} />);

    const pills = screen.getAllByRole('listitem');
    expect(pills).toHaveLength(5);

    // Done pills (0 and 1)
    expect(pills[0]).toHaveTextContent('P1');
    expect(pills[0]).toHaveAttribute('aria-label', 'Pregunta 1: success');
    expect(pills[1]).toHaveTextContent('P2');
    expect(pills[1]).toHaveAttribute('aria-label', 'Pregunta 2: success');

    // Active pill (2)
    expect(pills[2]).toHaveTextContent('P3');
    expect(pills[2]).toHaveAttribute('aria-label', 'Pregunta 3: generating');

    // Pending pills (3 and 4)
    expect(pills[3]).toHaveTextContent('P4');
    expect(pills[4]).toHaveTextContent('P5');
  });

  it('renders failed question status pill and failure count badge', () => {
    const failedProgress: GenerationProgress = {
      ...mockProgress,
      failed: 1,
      statuses: ['success', 'failed', 'generating', 'pending', 'pending'],
    };

    render(<QuestionGenerationProgress progress={failedProgress} />);

    const pills = screen.getAllByRole('listitem');
    expect(pills[0]).toHaveTextContent('P1');
    expect(pills[1]).toHaveTextContent('P2');
    expect(pills[2]).toHaveTextContent('P3');

    expect(screen.getByText(/1 pregunta\(s\) con error/)).toBeInTheDocument();
  });

  it('rotates pedagogical micro-captions beneath progress bar', () => {
    render(<QuestionGenerationProgress progress={mockProgress} />);

    expect(screen.getByText(PEDAGOGICAL_STAGES[0])).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(PROGRESS_ANIMATION.STAGE_SPEED_SECONDS * 1000);
    });

    expect(screen.getByText(PEDAGOGICAL_STAGES[1])).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(PROGRESS_ANIMATION.STAGE_SPEED_SECONDS * 1000);
    });

    expect(screen.getByText(PEDAGOGICAL_STAGES[2])).toBeInTheDocument();
  });

  it('increments elapsed timer and dynamically counts down remaining ETA', () => {
    render(<QuestionGenerationProgress progress={mockProgress} />);

    // 3 remaining questions * 12s = 36s
    expect(screen.getByText('~36s')).toBeInTheDocument();
    expect(screen.getByText('0s')).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(3000);
    });

    // Elapsed advances to 3s, remaining dynamically decrements to ~33s
    expect(screen.getByText('3s')).toBeInTheDocument();
    expect(screen.getByText('~33s')).toBeInTheDocument();
  });

  it('formats duration cleanly into Spanish text for elapsed and estimated times', () => {
    expect(formatDuration(null)).toBe('');
    expect(formatDuration(0, false)).toBe('0s');
    expect(formatDuration(45, false)).toBe('45s');
    expect(formatDuration(60, false)).toBe('1 min');
    expect(formatDuration(75, false)).toBe('1 min 15s');
    expect(formatDuration(45, true)).toBe('~45s');
    expect(formatDuration(60, true)).toBe('~1 min');
    expect(formatDuration(153, true)).toBe('~2 min 33s');
  });

  it('renders completed state when all questions are done or isComplete is true', () => {
    render(<QuestionGenerationProgress progress={{ ...mockProgress, done: 5 }} isComplete />);

    expect(screen.getByText('¡Preguntas listas para jugar!')).toBeInTheDocument();
    expect(screen.getByText('100%')).toBeInTheDocument();
    expect(screen.getByText('Preguntas y distractores pedagógicos verificados con éxito.')).toBeInTheDocument();
    const pills = screen.getAllByRole('listitem');
    expect(pills).toHaveLength(5);
    pills.forEach((pill) => expect(pill).toHaveTextContent(/P/));
  });

  it('preserves failed pills and reports partial counts when done with failures', () => {
    render(
      <QuestionGenerationProgress
        progress={{
          ...mockProgress,
          done: 5,
          total: 5,
          failed: 1,
          ids: ['q1', 'q2', 'q3', 'q4'],
          statuses: ['success', 'failed', 'success', 'success', 'success'],
        }}
        isComplete
      />
    );

    const pills = screen.getAllByRole('listitem');
    expect(pills).toHaveLength(5);
    expect(pills[0]).toHaveTextContent('P1');
    expect(pills[1]).toHaveTextContent('P2');
    expect(pills[2]).toHaveTextContent('P3');

    expect(
      screen.getByText('4 de 5 preguntas listas. 1 no salieron del modelo.')
    ).toBeInTheDocument();
    expect(screen.getByText(/1 pregunta\(s\) con error/)).toBeInTheDocument();
  });
});
