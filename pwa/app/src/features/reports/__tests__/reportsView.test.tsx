import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as httpClient from '../../../shared/api/httpClient';
import { ReportsView } from '../ReportsView';

const QUIZ = {
  start: '2026-11-09', end: '2026-11-16', students: 2, answers: 4, accuracy: 75,
  best_topic: 'arithmetic', weakest_topic: 'fractions', most_improved_topic: 'arithmetic',
  topics: [
    { topic: 'arithmetic', answers: 2, correct: 2, accuracy: 100, previous_accuracy: 0, change: 100 },
    { topic: 'fractions', answers: 2, correct: 1, accuracy: 50, previous_accuracy: 100, change: -50 },
  ],
  misconceptions: [{ misconception: 'added_denominators', topic: 'fractions', wrong_answers: 3 }],
};
const TUTOR = {
  start: '2026-11-10', end: '2026-11-11', students: 1, sessions: 1, turns: 6,
  most_asked_topic: 'arithmetic', most_stuck_topic: 'fractions',
  topics: [{ topic: 'arithmetic', turns: 5, students: 1, solved: 2, stuck: 0 }],
  session_summaries: [{
    student: 'ana', started_at: '2026-11-10 15:00:00', last_turn_at: '2026-11-10 15:06:00',
    turns: 6, topics: ['arithmetic', 'fractions'], solved: 2, stuck: 1,
  }],
};

function mockApi() {
  return vi.spyOn(httpClient, 'requestApi').mockImplementation(async (_m: string, path: string) =>
    path.startsWith('/quiz/analytics') ? QUIZ : TUTOR
  );
}

afterEach(() => vi.restoreAllMocks());

describe('ReportsView', () => {
  it('opens on the weekly quiz report with scores, change and misconceptions', async () => {
    const api = mockApi();
    render(<ReportsView />);
    await waitFor(() => expect(screen.getByText('Sumó los denominadores · Fracciones')).toBeInTheDocument());
    expect(api).toHaveBeenCalledWith('GET', '/quiz/analytics?period=week');
    expect(screen.getByText('75%')).toBeInTheDocument();
    expect(screen.getByText(/▼ 50 pts/)).toBeInTheDocument();
  });

  it('shows the daily tutor report as topics per session, without the chat', async () => {
    const api = mockApi();
    render(<ReportsView />);
    fireEvent.click(screen.getByRole('tab', { name: /Tutor/ }));
    fireEvent.click(screen.getByRole('tab', { name: /Día/ }));
    await waitFor(() => expect(screen.getByText('ana')).toBeInTheDocument());
    expect(api).toHaveBeenLastCalledWith('GET', '/tutor/analytics?period=day');
    expect(screen.getByText('Aritmética, Fracciones')).toBeInTheDocument();
    expect(screen.getByText('2 resueltos · 1 atorados')).toBeInTheDocument();
  });

  it('keeps the games tab as a placeholder without calling the backend', () => {
    const api = mockApi();
    render(<ReportsView />);
    api.mockClear();
    fireEvent.click(screen.getByRole('tab', { name: /Juegos/ }));
    expect(screen.getByText(/Próximamente/)).toBeInTheDocument();
    expect(api).not.toHaveBeenCalled();
  });

  it('says so when the period has no activity, and shows load errors', async () => {
    vi.spyOn(httpClient, 'requestApi').mockResolvedValueOnce({ ...QUIZ, answers: 0, topics: [] });
    const { unmount } = render(<ReportsView />);
    await waitFor(() => expect(screen.getByText('Sin actividad en este periodo.')).toBeInTheDocument());
    unmount();
    vi.spyOn(httpClient, 'requestApi').mockRejectedValue({ status: 500 });
    render(<ReportsView />);
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('No se pudo cargar el reporte'));
  });
});
