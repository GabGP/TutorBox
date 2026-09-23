import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import * as httpClient from '../../../shared/api/httpClient';
import { QuestionBankView } from '../QuestionBankView';
import { question } from './bankFixture';

describe('QuestionBankView loading, contract and editing', () => {
  it('shows skeleton rows while the next page loads', async () => {
    let resolvePage2!: (v: unknown) => void;
    vi.spyOn(httpClient, 'requestApi').mockImplementation(
      async (_m: string, path: string) => {
        if (path.startsWith('/quiz/topics')) return [];
        if (path.includes('offset=5'))
          return new Promise((res) => {
            resolvePage2 = res;
          });
        if (path.startsWith('/quiz/questions'))
          return { questions: [question], total: 25 };
        return {};
      }
    );
    render(<QuestionBankView />);
    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: '¿Cuánto es 27 + 15?' })
      ).toBeInTheDocument()
    );
    fireEvent.click(screen.getByRole('button', { name: 'Siguiente' }));
    // Layout holds: pageSize placeholders + busy flag instead of a flash.
    await waitFor(() =>
      expect(screen.getAllByTestId('bank-skeleton')).toHaveLength(5)
    );
    expect(
      screen.getByRole('list', { name: 'Banco de preguntas' })
    ).toHaveAttribute('aria-busy', 'true');
    await act(async () => {
      resolvePage2({ questions: [question], total: 25 });
    });
    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: '¿Cuánto es 27 + 15?' })
      ).toBeInTheDocument()
    );
    expect(screen.queryByTestId('bank-skeleton')).not.toBeInTheDocument();
    vi.restoreAllMocks();
  });

  it('toggles the JSON contract viewer for admins only', async () => {
    vi.spyOn(httpClient, 'requestApi').mockImplementation(
      async (_m: string, path: string) => {
        if (path === '/quiz/schema') return { title: 'quiz-question' };
        if (path.startsWith('/quiz/questions'))
          return { questions: [], total: 0 };
        return [];
      }
    );
    const { unmount } = render(<QuestionBankView isAdmin />);
    fireEvent.click(screen.getByText('Contrato JSON de preguntas'));
    await waitFor(() =>
      expect(screen.getByText(/quiz-question/)).toBeInTheDocument()
    );
    fireEvent.click(screen.getByText('Contrato JSON de preguntas'));
    await waitFor(() =>
      expect(screen.queryByText(/quiz-question/)).not.toBeInTheDocument()
    );
    unmount();
    vi.restoreAllMocks();

    render(<QuestionBankView />);
    await waitFor(() =>
      expect(screen.getByText(/No hay preguntas/)).toBeInTheDocument()
    );
    expect(
      screen.queryByText('Contrato JSON de preguntas')
    ).not.toBeInTheDocument();
  });

  it('edits a question via PUT with prefilled form', async () => {
    const calls: Array<[string, string, unknown?]> = [];
    vi.spyOn(httpClient, 'requestApi').mockImplementation(
      async (m: string, path: string, body?: unknown) => {
        calls.push([m, path, body]);
        if (m === 'PUT') return { ...question, question_text: 'Editada' };
        if (path.startsWith('/quiz/questions'))
          return { questions: [question], total: 1 };
        return [];
      }
    );
    render(<QuestionBankView />);
    await waitFor(() =>
      expect(screen.getByText('¿Cuánto es 27 + 15?')).toBeInTheDocument()
    );
    fireEvent.click(screen.getByRole('button', { name: 'Editar pregunta q1' }));
    expect(screen.getByText('Editar pregunta')).toBeInTheDocument();
    expect(screen.getByDisplayValue('¿Cuánto es 27 + 15?')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }));
    await waitFor(() =>
      expect(
        calls.some(([m, p]) => m === 'PUT' && p === '/quiz/questions/q1')
      ).toBe(true)
    );
    vi.restoreAllMocks();
  });

  it('floats bank load failures as error toasts', async () => {
    vi.spyOn(httpClient, 'requestApi').mockImplementation(
      async (_m: string, path: string) => {
        if (path.startsWith('/quiz/topics')) return [];
        throw { status: 500 };
      }
    );
    render(<QuestionBankView />);
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(
        'Error al cargar preguntas'
      )
    );
    vi.restoreAllMocks();
  });
});
