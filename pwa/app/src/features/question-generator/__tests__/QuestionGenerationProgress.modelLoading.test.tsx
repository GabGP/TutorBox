import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import type { GenerationProgress } from '../generator.types';
import { QuestionGenerationProgress } from '../QuestionGenerationProgress';

const LOADING = 'Cargando el modelo de preguntas…';

function progressWith(overrides: Partial<GenerationProgress>): GenerationProgress {
  return {
    done: 0,
    total: 2,
    failed: 0,
    ids: [],
    eta: 12,
    currentTopic: 'arithmetic',
    currentSubconcept: null,
    statuses: ['pending', 'pending'],
    ...overrides,
  };
}

describe('QuestionGenerationProgress while the quiz model loads', () => {
  it('shows a spinner with the loading text and an indeterminate bar instead of the progress bar', () => {
    render(<QuestionGenerationProgress progress={progressWith({ modelLoading: true })} />);

    expect(screen.getByRole('status', { name: LOADING })).toBeInTheDocument();
    expect(screen.getByText(LOADING)).toBeInTheDocument();
    expect(screen.queryByRole('progressbar')).toBeNull();
  });

  it('switches to the per-question progress once the model is ready', () => {
    const { rerender } = render(<QuestionGenerationProgress progress={progressWith({ modelLoading: true })} />);

    rerender(<QuestionGenerationProgress progress={progressWith({ modelLoading: false })} />);

    expect(screen.queryByRole('status')).toBeNull();
    expect(screen.getByRole('progressbar', { name: 'Progreso general' })).toBeInTheDocument();
  });

  it('shows the normal progress when the flag is absent', () => {
    render(<QuestionGenerationProgress progress={progressWith({})} />);

    expect(screen.queryByRole('status')).toBeNull();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });
});
