import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import * as httpClient from '../../../shared/api/httpClient';
import { advanceHold, setupHoldTimers, teardownHoldTimers } from '../../../test/holdTimers';
import { QuestionBankView } from '../QuestionBankView';
import { question } from './bankFixture';

async function waitForRealTimers(assertion: () => void) {
  await waitFor(assertion);
}

describe('QuestionBankView hold-to-confirm delete', () => {
  it('arms delete on swipe tap then commits on hold (2000ms)', async () => {
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
    await waitForRealTimers(() =>
      expect(screen.getByText('¿Cuánto es 27 + 15?')).toBeInTheDocument()
    );
    setupHoldTimers();
    try {
      fireEvent.click(screen.getByRole('button', { name: 'Eliminar' }));
      const holdBtn = screen.getByRole('button', {
        name: 'Mantén para eliminar pregunta q1',
      });
      fireEvent.pointerDown(holdBtn, { pointerId: 1 });
      advanceHold(2000);
      await act(async () => {});
      expect(calls).toContain('DELETE /quiz/questions/q1');
    } finally {
      teardownHoldTimers();
    }
    vi.restoreAllMocks();
  });

  it('deselects a selected question once the hold commits', async () => {
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
    await waitForRealTimers(() =>
      expect(
        screen.getByRole('button', { name: '¿Cuánto es 27 + 15?' })
      ).toBeInTheDocument()
    );
    expect(screen.getByText('1 elegidas · 1')).toBeInTheDocument();
    setupHoldTimers();
    try {
      fireEvent.click(screen.getByRole('button', { name: 'Eliminar' }));
      const holdBtn = screen.getByRole('button', {
        name: 'Mantén para eliminar pregunta q1',
      });
      fireEvent.pointerDown(holdBtn, { pointerId: 1 });
      advanceHold(2000);
      await act(async () => {});
      expect(onToggleSelect).toHaveBeenCalledWith('q1');
    } finally {
      teardownHoldTimers();
    }
    vi.restoreAllMocks();
  });

  it('cancels the armed delete without deleting', async () => {
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
    // Full-row swap: the strip is gone, HoldButton + Cancelar take its place.
    expect(screen.queryByRole('button', { name: 'Info' })).not.toBeInTheDocument();
    fireEvent.click(
      screen.getByRole('button', { name: 'Cancelar eliminación pregunta q1' })
    );
    expect(
      screen.queryByRole('button', { name: 'Mantén para eliminar pregunta q1' })
    ).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Eliminar' })).toBeInTheDocument();
    expect(calls).not.toContain('DELETE /quiz/questions/q1');
    vi.restoreAllMocks();
  });

  it('disarms the armed delete on Escape without deleting', async () => {
    vi.spyOn(httpClient, 'requestApi').mockImplementation(
      async (_m: string, path: string) => {
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
      screen.getByRole('button', { name: 'Mantén para eliminar pregunta q1' })
    ).toBeInTheDocument();
    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    });
    expect(
      screen.queryByRole('button', { name: 'Mantén para eliminar pregunta q1' })
    ).not.toBeInTheDocument();
    vi.restoreAllMocks();
  });
});
