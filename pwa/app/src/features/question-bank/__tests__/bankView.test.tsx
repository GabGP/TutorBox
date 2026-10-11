import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import * as httpClient from '../../../shared/api/httpClient';
import { QuestionBankView } from '../QuestionBankView';
import { question } from './bankFixture';

describe('QuestionBankView browsing and selection', () => {
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

  it('opens detail via Info without selecting in select mode', async () => {
    const onToggleSelect = vi.fn();
    vi.spyOn(httpClient, 'requestApi').mockImplementation(
      async (_m: string, path: string) => {
        if (path.startsWith('/quiz/topics')) return [];
        if (path === '/quiz/questions/q1') return question;
        if (path.startsWith('/quiz/questions'))
          return { questions: [question], total: 1 };
        return {};
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
    expect(onToggleSelect).not.toHaveBeenCalled();
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
    expect(body).toContain('B: 42');
    expect(body).not.toContain('B ✔:');
    expect(
      screen.getByRole('dialog', { name: 'Detalle pregunta q1' }).querySelector('svg')
    ).toBeInTheDocument();
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

  it('opens the strip with a short drag, then taps Info', async () => {
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

  it('unfolds options with explanations on row tap in select mode', async () => {
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
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument();
    const face = screen.getByRole('button', { name: '¿Cuánto es 27 + 15?' });
    fireEvent.click(face);
    expect(face).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByLabelText('Opción A')).toHaveValue('32');
    expect(screen.getByLabelText('Opción B')).toHaveValue('42');
    expect(screen.getByLabelText('Explicación A')).toHaveValue('Olvidó la llevada');
    expect(screen.queryByLabelText('Explicación B')).not.toBeInTheDocument();
    expect(screen.getByText('Respuesta correcta')).toBeInTheDocument();
    // Opening never selects; selection is the explicit toggle.
    expect(onToggleSelect).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: /Usar en el juego/ }));
    expect(onToggleSelect).toHaveBeenCalledWith('q1');
    fireEvent.click(face);
    expect(screen.queryByLabelText('Opción A')).not.toBeInTheDocument();
    vi.restoreAllMocks();
  });

  it('saves inline edits back to the bank', async () => {
    const calls: { m: string; path: string; body?: unknown }[] = [];
    vi.spyOn(httpClient, 'requestApi').mockImplementation(
      async (m: string, path: string, body?: unknown) => {
        calls.push({ m, path, body });
        if (m === 'PUT') return { ...question, ...(body as object) };
        if (path.startsWith('/quiz/questions'))
          return { questions: [question], total: 1 };
        return [];
      }
    );
    render(<QuestionBankView selectable selectedIds={['q1']} onToggleSelect={vi.fn()} />);
    await waitFor(() =>
      expect(screen.getByText('¿Cuánto es 27 + 15?')).toBeInTheDocument()
    );
    expect(screen.getByText('En el juego')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '¿Cuánto es 27 + 15?' }));
    const save = screen.getByRole('button', { name: 'Guardar' });
    expect(save).toBeDisabled();
    expect(screen.getByRole('button', { name: /Quitar del juego/ })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Opción D'), { target: { value: '44' } });
    fireEvent.change(screen.getByLabelText('Explicación D'), {
      target: { value: 'Sumó dos de más' },
    });
    expect(save).toBeEnabled();
    fireEvent.click(save);
    await waitFor(() =>
      expect(screen.getByText('Pregunta guardada en el banco.')).toBeInTheDocument()
    );
    const put = calls.find((c) => c.m === 'PUT');
    expect(put?.path).toBe('/quiz/questions/q1');
    expect(put?.body).toMatchObject({
      id: 'q1',
      correct_option: 'B',
      options: { A: '32', B: '42', C: '41', D: '44' },
      distractors: {
        A: { misconception: 'no-lleva', explanation: 'Olvidó la llevada' },
        D: { misconception: 'conteo', explanation: 'Sumó dos de más' },
      },
    });
    expect(screen.getByRole('button', { name: 'Guardar' })).toBeDisabled();
    vi.restoreAllMocks();
  });
});
