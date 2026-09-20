import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import * as httpClient from '../../../shared/api/httpClient';
import { bankApi } from '../bankApi';
import { QuestionBankView } from '../QuestionBankView';
import { QuestionForm } from '../QuestionForm';
import { generatorApi } from '../../question-generator/generatorApi';

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
  it('listQuestions defaults to 5 rows per page', async () => {
    const spy = vi
      .spyOn(httpClient, 'requestApi')
      .mockResolvedValue({ questions: [], total: 0 });
    await bankApi.listQuestions({ topic: 'sumas', offset: 0 });
    expect(spy).toHaveBeenCalledWith(
      'GET',
      '/quiz/questions?topic=sumas&limit=5&offset=0'
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

describe('QuestionForm taxonomy selects', () => {
  const taxonomy = [
    {
      name: 'arithmetic',
      label: 'Aritmética',
      subconcepts: [
        {
          name: 'addition_subtraction',
          misconceptions: ['sign_error', 'borrowing_error'],
        },
        {
          name: 'multiplication_division',
          misconceptions: ['forgot_carry'],
        },
      ],
    },
  ];

  it('offers subconcepts and misconceptions from the chosen topic', async () => {
    vi.spyOn(generatorApi, 'getTopics').mockResolvedValue(taxonomy);
    render(<QuestionForm initial={null} onSaved={() => {}} />);
    await waitFor(() =>
      expect(
        screen.getByRole('option', { name: 'Aritmética' })
      ).toBeInTheDocument()
    );
    fireEvent.change(screen.getByLabelText('Tema'), {
      target: { value: 'arithmetic' },
    });
    const sub = screen.getByLabelText('Subconcepto');
    expect(sub.tagName).toBe('SELECT');
    const subTexts = Array.from((sub as HTMLSelectElement).options).map(
      (o) => o.text
    );
    expect(subTexts).toContain('Suma y resta');
    expect(subTexts).toContain('Multiplicación y división');

    fireEvent.change(sub, { target: { value: 'addition_subtraction' } });
    for (const k of ['B', 'C', 'D']) {
      const misc = screen.getByLabelText(`Error ${k}`);
      expect(misc.tagName).toBe('SELECT');
      const values = Array.from((misc as HTMLSelectElement).options).map(
        (o) => o.value
      );
      expect(values).toContain('sign_error');
      expect(values).toContain('borrowing_error');
    }
    vi.restoreAllMocks();
  });

  it('resets the subconcept when the topic changes away', async () => {
    vi.spyOn(generatorApi, 'getTopics').mockResolvedValue(taxonomy);
    render(<QuestionForm initial={null} onSaved={() => {}} />);
    await waitFor(() =>
      expect(
        screen.getByRole('option', { name: 'Aritmética' })
      ).toBeInTheDocument()
    );
    fireEvent.change(screen.getByLabelText('Tema'), {
      target: { value: 'arithmetic' },
    });
    fireEvent.change(screen.getByLabelText('Subconcepto'), {
      target: { value: 'addition_subtraction' },
    });
    expect(screen.getByLabelText('Subconcepto')).toHaveValue(
      'addition_subtraction'
    );
    fireEvent.change(screen.getByLabelText('Tema'), {
      target: { value: '' },
    });
    expect(screen.getByLabelText('Subconcepto')).toHaveValue('');
    vi.restoreAllMocks();
  });

  it('preserves edit values missing from the taxonomy with text fallback', async () => {
    vi.spyOn(generatorApi, 'getTopics').mockResolvedValue([]);
    render(<QuestionForm initial={question} onSaved={() => {}} />);
    // Stale topic/subconcept stay selectable so edits never lose data.
    expect(screen.getByLabelText('Tema')).toHaveValue('sumas');
    expect(screen.getByLabelText('Subconcepto')).toHaveValue('llevar');
    // No taxonomy for (sumas, llevar): misconceptions stay free text.
    const miscA = screen.getByLabelText('Error A');
    expect(miscA.tagName).toBe('INPUT');
    expect(miscA).toHaveValue('no-lleva');
    vi.restoreAllMocks();
  });
});

describe('QuestionBankView', () => {
  it('lists questions and opens detail sheet', async () => {
    vi.spyOn(httpClient, 'requestApi').mockImplementation(
      async (_m: string, path: string) => {
        if (path.startsWith('/quiz/topics')) return [];
        if (path === '/quiz/questions/q1') return question;
        if (path.startsWith('/quiz/questions'))
          return { questions: [question], total: 1 };
        return {};
      }
    );
    render(<QuestionBankView />);
    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: '¿Cuánto es 27 + 15?' })
      ).toBeInTheDocument()
    );
    fireEvent.click(
      screen.getByRole('button', { name: '¿Cuánto es 27 + 15?' })
    );
    await waitFor(() =>
      expect(screen.getByText(/Olvidó la llevada/)).toBeInTheDocument()
    );
    expect(
      screen.getByRole('dialog', { name: 'Detalle pregunta q1' })
    ).toBeInTheDocument();
    vi.restoreAllMocks();
  });

  it('opens detail via swipe Info action', async () => {
    vi.spyOn(httpClient, 'requestApi').mockImplementation(
      async (_m: string, path: string) => {
        if (path.startsWith('/quiz/topics')) return [];
        if (path === '/quiz/questions/q1') return question;
        if (path.startsWith('/quiz/questions'))
          return { questions: [question], total: 1 };
        return {};
      }
    );
    render(<QuestionBankView />);
    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: 'Ver detalle pregunta q1' })
      ).toBeInTheDocument()
    );
    fireEvent.click(
      screen.getByRole('button', { name: 'Ver detalle pregunta q1' })
    );
    await waitFor(() =>
      expect(screen.getByText(/Olvidó la llevada/)).toBeInTheDocument()
    );
    vi.restoreAllMocks();
  });

  it('marks the correct answer to the right of the option text', async () => {
    vi.spyOn(httpClient, 'requestApi').mockImplementation(
      async (_m: string, path: string) => {
        if (path.startsWith('/quiz/topics')) return [];
        if (path === '/quiz/questions/q1') return question;
        if (path.startsWith('/quiz/questions'))
          return { questions: [question], total: 1 };
        return {};
      }
    );
    render(<QuestionBankView />);
    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: 'Ver detalle pregunta q1' })
      ).toBeInTheDocument()
    );
    fireEvent.click(
      screen.getByRole('button', { name: 'Ver detalle pregunta q1' })
    );
    await waitFor(() =>
      expect(
        screen.getByRole('dialog', { name: 'Detalle pregunta q1' })
      ).toBeInTheDocument()
    );
    const body =
      screen.getByRole('dialog', { name: 'Detalle pregunta q1' }).textContent ??
      '';
    expect(body).toContain('B: 42 ✔');
    expect(body).not.toContain('B ✔:');
    vi.restoreAllMocks();
  });

  it('requests 5 rows per page by default and supports page-size selector', async () => {
    const calls: string[] = [];
    vi.spyOn(httpClient, 'requestApi').mockImplementation(
      async (_m: string, path: string) => {
        calls.push(path);
        if (path.startsWith('/quiz/topics')) return [];
        if (path.startsWith('/quiz/questions'))
          return { questions: [question], total: 25 };
        return {};
      }
    );
    render(<QuestionBankView />);
    await waitFor(() =>
      expect(
        calls.some((p) => p.includes('limit=5&offset=0'))
      ).toBe(true)
    );
    expect(screen.getByText('1/5')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Filas por página'), {
      target: { value: '20' },
    });
    await waitFor(() =>
      expect(
        calls.some((p) => p.includes('limit=20&offset=0'))
      ).toBe(true)
    );
    fireEvent.change(screen.getByLabelText('Filas por página'), {
      target: { value: '5' },
    });
    await waitFor(() =>
      expect(
        calls.some((p) => p.includes('limit=5&offset=0'))
      ).toBe(true)
    );
    vi.restoreAllMocks();
  });

  it('fetches fresh detail on open via GET /quiz/questions/{id}', async () => {
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
      expect(
        screen.getByRole('button', { name: '¿Cuánto es 27 + 15?' })
      ).toBeInTheDocument()
    );
    fireEvent.click(
      screen.getByRole('button', { name: '¿Cuánto es 27 + 15?' })
    );
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

  it('deselects a selected question once deleted', async () => {
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
        selectedIds={['q1']}
        onToggleSelect={onToggleSelect}
      />
    );
    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: '¿Cuánto es 27 + 15?' })
      ).toBeInTheDocument()
    );
    expect(screen.getByText('1 elegidas · 1')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Eliminar' }));
    fireEvent.click(screen.getByRole('button', { name: '¿Confirmar?' }));
    await waitFor(() =>
      expect(onToggleSelect).toHaveBeenCalledWith('q1')
    );
    vi.restoreAllMocks();
  });

  it('toggles selection in select mode via checkbox and row tap', async () => {
    vi.spyOn(httpClient, 'requestApi').mockImplementation(
      async (_m: string, path: string) => {
        if (path.startsWith('/quiz/topics')) return [];
        if (path === '/quiz/questions/q1') return question;
        if (path.startsWith('/quiz/questions'))
          return { questions: [question], total: 1 };
        return {};
      }
    );
    render(<QuestionBankView />);
    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: '¿Cuánto es 27 + 15?' })
      ).toBeInTheDocument()
    );
    const faceBtn = screen.getByRole('button', {
      name: '¿Cuánto es 27 + 15?',
    });
    const face = faceBtn.parentElement!;
    const root = face.parentElement!;
    Object.defineProperty(root, 'offsetWidth', {
      value: 300,
      configurable: true,
    });
    Object.defineProperty(root.firstElementChild!, 'offsetWidth', {
      value: 192,
      configurable: true,
    });
    // Open the strip with a short drag, then tap Info.
    fireEvent.pointerDown(face, { clientX: 250 });
    fireEvent.pointerMove(face, { clientX: 200 });
    fireEvent.pointerUp(face, { clientX: 200 });
    await waitFor(() => expect(root).toHaveAttribute('data-open', 'true'));
    fireEvent.click(
      screen.getByRole('button', { name: 'Ver detalle pregunta q1' })
    );
    await waitFor(() =>
      expect(
        screen.getByRole('dialog', { name: 'Detalle pregunta q1' })
      ).toBeInTheDocument()
    );
    // Same as Edit: the strip stays open behind the sheet.
    expect(root).toHaveAttribute('data-open', 'true');
    vi.restoreAllMocks();
  });

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

  it('toggles selection in select mode via checkbox and row tap', async () => {
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
    fireEvent.click(screen.getByRole('button', { name: '¿Cuánto es 27 + 15?' }));
    expect(onToggleSelect).toHaveBeenCalledTimes(2);
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
