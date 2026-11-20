import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import * as httpClient from '../../../shared/api/httpClient';
import { BankPickStep } from '../BankPickStep';

function mockBankBackend() {
  vi.spyOn(httpClient, 'requestApi').mockImplementation(
    async (_m: string, path: string) => {
      if (path.startsWith('/quiz/topics')) return [];
      if (path.startsWith('/quiz/questions'))
        return { questions: [], total: 0 };
      if (path.startsWith('/quiz/generation-metrics'))
        return {
          total_generations: 0,
          successful_generations: 0,
          failed_generations: 0,
          success_rate: 0,
          avg_attempts: 0,
          avg_duration_ms: 0,
        };
      if (path.startsWith('/quiz/generation-logs')) return { logs: [], total: 0 };
      return {};
    }
  );
}

const baseProps = {
  selectedTopic: 'arithmetic',
  count: 5,
  onChangeCount: vi.fn(),
  genError: null,
  progress: null,
  pregenerating: false,
  bankIds: [],
  onToggleBankId: vi.fn(),
  onEnsureBankIds: vi.fn(),
  onPregenerate: vi.fn().mockResolvedValue(['q1']),
};

describe('BankPickStep', () => {
  it('shows the picker subtabs with Elegir first', async () => {
    mockBankBackend();
    render(<BankPickStep {...baseProps} />);
    expect(
      screen.getByRole('tab', { name: /Elegir/ })
    ).toHaveAttribute('aria-selected', 'true');
    await waitFor(() =>
      expect(screen.getByText(/sin generar/)).toBeInTheDocument()
    );
    vi.restoreAllMocks();
  });

  it('opens the create form under Crear', async () => {
    mockBankBackend();
    render(<BankPickStep {...baseProps} />);
    fireEvent.click(screen.getByRole('tab', { name: /Crear/ }));
    expect(screen.getByText('Nueva pregunta')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Guardar' })
    ).toBeInTheDocument();
    vi.restoreAllMocks();
  });

  it('floats pre-generation errors as error toasts', async () => {
    mockBankBackend();
    render(<BankPickStep {...baseProps} genError="El modelo no respondió" />);
    expect(screen.getByRole('alert')).toHaveTextContent(
      'El modelo no respondió'
    );
    vi.restoreAllMocks();
  });

  it('pre-generates from the Pre-generar tab', async () => {
    mockBankBackend();
    const onPregenerate = vi.fn().mockResolvedValue(['q9']);
    const onEnsureBankIds = vi.fn();
    render(
      <BankPickStep {...baseProps} onPregenerate={onPregenerate} onEnsureBankIds={onEnsureBankIds} />
    );
    fireEvent.click(screen.getByRole('tab', { name: /Pre-generar/ }));
    fireEvent.click(
      screen.getByRole('button', { name: /Pre-generar en banco/ })
    );
    await waitFor(() => expect(onPregenerate).toHaveBeenCalled());
    await waitFor(() => expect(onEnsureBankIds).toHaveBeenCalledWith(['q9']));
    vi.restoreAllMocks();
  });

  it('offers Detener while pre-generating, then Cancelar and Reanudar', () => {
    mockBankBackend();
    const controls = {
      onStopPregeneration: vi.fn(),
      onResumePregeneration: vi.fn(),
      onCancelPregeneration: vi.fn(),
    };
    const progress = { done: 1, total: 3, failed: 0, ids: ['q1'], eta: 5, currentIndex: 2 };
    const { rerender } = render(
      <BankPickStep {...baseProps} {...controls} progress={progress} pregenerating />
    );
    fireEvent.click(screen.getByRole('tab', { name: /Pre-generar/ }));

    expect(screen.queryByRole('button', { name: /Pre-generar en banco/ })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Detener' }));
    expect(controls.onStopPregeneration).toHaveBeenCalledTimes(1);

    rerender(
      <BankPickStep
        {...baseProps}
        {...controls}
        progress={progress}
        pregenerating
        pregenerationPaused
      />
    );
    expect(screen.getByRole('heading', { name: 'Creación detenida' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Reanudar' }));
    fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }));
    expect(controls.onResumePregeneration).toHaveBeenCalledTimes(1);
    expect(controls.onCancelPregeneration).toHaveBeenCalledTimes(1);
    vi.restoreAllMocks();
  });
});
