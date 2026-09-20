import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import * as httpClient from '../../../shared/api/httpClient';
import { bankApi } from '../bankApi';
import { QuestionBankView } from '../QuestionBankView';

const question = {
  id: 'q1',
  topic: 'sumas',
  subconcept: 'llevar',
  question_text: '¿Cuánto es 27 + 15?',
  options: { A: '32', B: '42', C: '41', D: '43' },
  correct_option: 'B',
  distractors: {
    A: { misconception: 'no-lleva', explanation: 'Olvidó la llevada' },
    C: { misconception: 'resta', explanation: 'Restó en vez de sumar' },
    D: { misconception: 'conteo', explanation: 'Contó de más' },
  },
};

describe('bankApi', () => {
  it('listQuestions builds query params', async () => {
    const spy = vi
      .spyOn(httpClient, 'requestApi')
      .mockResolvedValue({ questions: [], total: 0 });
    await bankApi.listQuestions({ topic: 'sumas', limit: 20, offset: 0 });
    expect(spy).toHaveBeenCalledWith(
      'GET',
      '/quiz/questions?topic=sumas&limit=20&offset=0'
    );
    spy.mockRestore();
  });

  it('validateQuestion posts the question envelope', async () => {
    const spy = vi
      .spyOn(httpClient, 'requestApi')
      .mockResolvedValue({ is_valid: true, errors: [], details: {} });
    await bankApi.validateQuestion(question);
    expect(spy).toHaveBeenCalledWith('POST', '/quiz/validate', {
      question,
    });
    spy.mockRestore();
  });

  it('deleteQuestion sends DELETE', async () => {
    const spy = vi.spyOn(httpClient, 'requestApi').mockResolvedValue({});
    await bankApi.deleteQuestion('q1');
    expect(spy).toHaveBeenCalledWith('DELETE', '/quiz/questions/q1');
    spy.mockRestore();
  });

  it('updateQuestion sends PUT', async () => {
    const spy = vi
      .spyOn(httpClient, 'requestApi')
      .mockResolvedValue({ ...question });
    await bankApi.updateQuestion('q1', { ...question, id: 'q1' });
    expect(spy).toHaveBeenCalledWith(
      'PUT',
      '/quiz/questions/q1',
      expect.objectContaining({ id: 'q1' })
    );
    spy.mockRestore();
  });

  it('getSchema fetches the contract', async () => {
    const spy = vi.spyOn(httpClient, 'requestApi').mockResolvedValue({});
    await bankApi.getSchema();
    expect(spy).toHaveBeenCalledWith('GET', '/quiz/schema');
    spy.mockRestore();
  });
});

describe('QuestionBankView', () => {
  it('lists questions and expands detail', async () => {
    vi.spyOn(httpClient, 'requestApi').mockImplementation(
      async (_m: string, path: string) => {
        if (path.startsWith('/quiz/topics')) return [];
        if (path.startsWith('/quiz/questions'))
          return { questions: [question], total: 1 };
        return {};
      }
    );
    render(<QuestionBankView />);
    await waitFor(() =>
      expect(screen.getByText('¿Cuánto es 27 + 15?')).toBeInTheDocument()
    );
    fireEvent.click(screen.getByText('¿Cuánto es 27 + 15?'));
    expect(screen.getByText(/Olvidó la llevada/)).toBeInTheDocument();
    vi.restoreAllMocks();
  });

  it('fetches fresh detail on expand via GET /quiz/questions/{id}', async () => {
    const calls: string[] = [];
    vi.spyOn(httpClient, 'requestApi').mockImplementation(
      async (m: string, path: string) => {
        calls.push(`${m} ${path}`);
        if (path === '/quiz/questions/q1') return question;
        if (path.startsWith('/quiz/questions'))
          return { questions: [question], total: 1 };
        return [];
      }
    );
    render(<QuestionBankView />);
    await waitFor(() =>
      expect(screen.getByText('¿Cuánto es 27 + 15?')).toBeInTheDocument()
    );
    fireEvent.click(screen.getByText('¿Cuánto es 27 + 15?'));
    await waitFor(() => expect(calls).toContain('GET /quiz/questions/q1'));
    vi.restoreAllMocks();
  });

  it('asks delete confirmation before deleting', async () => {
    const calls: string[] = [];
    vi.spyOn(httpClient, 'requestApi').mockImplementation(
      async (m: string, path: string) => {
        calls.push(`${m} ${path}`);
        if (path.startsWith('/quiz/questions'))
          return { questions: [question], total: 1 };
        return [];
      }
    );
    render(<QuestionBankView />);
    await waitFor(() =>
      expect(screen.getByText('¿Cuánto es 27 + 15?')).toBeInTheDocument()
    );
    fireEvent.click(screen.getByRole('button', { name: 'Eliminar' }));
    expect(
      screen.getByRole('button', { name: '¿Confirmar?' })
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '¿Confirmar?' }));
    await waitFor(() =>
      expect(calls).toContain('DELETE /quiz/questions/q1')
    );
    vi.restoreAllMocks();
  });

  it('toggles selection in select mode', async () => {
    const onToggleSelect = vi.fn();
    vi.spyOn(httpClient, 'requestApi').mockImplementation(
      async (_m: string, path: string) => {
        if (path.startsWith('/quiz/questions'))
          return { questions: [question], total: 1 };
        return [];
      }
    );
    render(
      <QuestionBankView
        selectable
        selectedIds={[]}
        onToggleSelect={onToggleSelect}
      />
    );
    await waitFor(() =>
      expect(screen.getByText('¿Cuánto es 27 + 15?')).toBeInTheDocument()
    );
    fireEvent.click(screen.getByRole('checkbox', { name: 'Elegir pregunta q1' }));
    expect(onToggleSelect).toHaveBeenCalledWith('q1');
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
});
