import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as httpClient from '../../../shared/api/httpClient';
import { QuestionBankView } from '../QuestionBankView';
import { question } from './bankFixture';

const secondQuestion = { ...question, id: 'q2', question_text: '¿Cuánto es 9 × 3?' };

function mockTwoQuestions() {
  vi.spyOn(httpClient, 'requestApi').mockImplementation(
    async (_m: string, path: string) => {
      if (path.startsWith('/quiz/questions'))
        return { questions: [question, secondQuestion], total: 2 };
      return [];
    }
  );
}

describe('QuestionBankView Seleccionar mode', () => {
  afterEach(() => vi.restoreAllMocks());

  it('picks several questions with one tap each until Listo', async () => {
    mockTwoQuestions();
    const onToggleSelect = vi.fn();
    render(<QuestionBankView selectable selectedIds={[]} onToggleSelect={onToggleSelect} />);
    await screen.findByText('¿Cuánto es 9 × 3?');

    const selectButton = screen.getByRole('button', { name: 'Seleccionar' });
    expect(selectButton).toHaveAttribute('aria-pressed', 'false');
    fireEvent.click(selectButton);
    expect(screen.getByRole('button', { name: 'Listo' })).toHaveAttribute('aria-pressed', 'true');

    fireEvent.click(screen.getByRole('button', { name: '¿Cuánto es 27 + 15?' }));
    fireEvent.click(screen.getByRole('button', { name: '¿Cuánto es 9 × 3?' }));

    expect(onToggleSelect).toHaveBeenNthCalledWith(1, 'q1');
    expect(onToggleSelect).toHaveBeenNthCalledWith(2, 'q2');
    // A tap selects; it never unfolds the options editor in this mode.
    expect(screen.queryByLabelText('Opción A')).toBeNull();
  });

  it('shows which questions are chosen and goes back to unfolding after Listo', async () => {
    mockTwoQuestions();
    const onToggleSelect = vi.fn();
    render(<QuestionBankView selectable selectedIds={['q1']} onToggleSelect={onToggleSelect} />);
    await screen.findByText('¿Cuánto es 9 × 3?');
    fireEvent.click(screen.getByRole('button', { name: 'Seleccionar' }));

    expect(screen.getByRole('button', { name: '¿Cuánto es 27 + 15?' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: '¿Cuánto es 9 × 3?' })).toHaveAttribute('aria-pressed', 'false');

    fireEvent.click(screen.getByRole('button', { name: 'Listo' }));
    const face = screen.getByRole('button', { name: '¿Cuánto es 27 + 15?' });
    fireEvent.click(face);
    expect(face).toHaveAttribute('aria-expanded', 'true');
    expect(onToggleSelect).not.toHaveBeenCalled();
  });

  it('keeps swiping in Seleccionar mode', async () => {
    mockTwoQuestions();
    render(<QuestionBankView selectable selectedIds={[]} onToggleSelect={vi.fn()} />);
    await screen.findByText('¿Cuánto es 9 × 3?');
    fireEvent.click(screen.getByRole('button', { name: 'Seleccionar' }));

    expect(screen.getByRole('button', { name: 'Editar pregunta q1' })).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Mostrar acciones' })).toHaveLength(2);
  });

  it('has no Seleccionar button outside the quiz-prep picker', async () => {
    mockTwoQuestions();
    render(<QuestionBankView />);
    await waitFor(() => expect(screen.getByText('¿Cuánto es 9 × 3?')).toBeInTheDocument());
    expect(screen.queryByRole('button', { name: 'Seleccionar' })).toBeNull();
  });
});
