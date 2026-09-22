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
});
