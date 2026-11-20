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
  generating: false,
  bankIds: [],
  onToggleBankId: vi.fn(),
  onEnsureBankIds: vi.fn(),
  onGenerate: vi.fn().mockResolvedValue(['q1']),
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

  it('floats generation errors as error toasts', async () => {
    mockBankBackend();
    render(<BankPickStep {...baseProps} genError="El modelo no respondió" />);
    expect(screen.getByRole('alert')).toHaveTextContent(
      'El modelo no respondió'
    );
    vi.restoreAllMocks();
  });

  it('generates into the bank from the Generar tab', async () => {
    mockBankBackend();
    const onGenerate = vi.fn().mockResolvedValue(['q9']);
    const onEnsureBankIds = vi.fn();
    render(
      <BankPickStep {...baseProps} onGenerate={onGenerate} onEnsureBankIds={onEnsureBankIds} />
    );
    fireEvent.click(screen.getByRole('tab', { name: /^Generar$/ }));
    fireEvent.click(
      screen.getByRole('button', { name: /Generar en banco/ })
    );
    await waitFor(() => expect(onGenerate).toHaveBeenCalled());
    await waitFor(() => expect(onEnsureBankIds).toHaveBeenCalledWith(['q9']));
    vi.restoreAllMocks();
  });

  it('offers Detener while generating, then Cancelar and Reanudar', () => {
    mockBankBackend();
    const controls = {
      onStopGeneration: vi.fn(),
      onResumeGeneration: vi.fn(),
      onCancelGeneration: vi.fn(),
    };
    const progress = { done: 1, total: 3, failed: 0, ids: ['q1'], eta: 5, currentIndex: 2 };
    const { rerender } = render(
      <BankPickStep {...baseProps} {...controls} progress={progress} generating />
    );
    fireEvent.click(screen.getByRole('tab', { name: /^Generar$/ }));

    expect(screen.queryByRole('button', { name: /Generar en banco/ })).not.toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'Progreso de creación de preguntas' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Generar una más' })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Detener' }));
    expect(controls.onStopGeneration).toHaveBeenCalledTimes(1);

    rerender(
      <BankPickStep
        {...baseProps}
        {...controls}
        progress={progress}
        generating
        generationPaused
      />
    );
    expect(screen.getByRole('heading', { name: 'Creación detenida' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Reanudar' }));
    fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }));
    expect(controls.onResumeGeneration).toHaveBeenCalledTimes(1);
    expect(controls.onCancelGeneration).toHaveBeenCalledTimes(1);

    // Cancelar clears the progress in the coordinator, so the counter comes back.
    rerender(<BankPickStep {...baseProps} {...controls} progress={null} />);
    expect(screen.getByRole('button', { name: 'Generar una más' })).toBeInTheDocument();
    expect(screen.queryByRole('region', { name: 'Progreso de creación de preguntas' })).toBeNull();
    vi.restoreAllMocks();
  });

  it('keeps a finished result on screen until Generar más', () => {
    mockBankBackend();
    const onGenerateMore = vi.fn();
    const finished = {
      done: 3,
      total: 3,
      failed: 1,
      ids: ['q1', 'q2'],
      eta: 5,
      currentIndex: 3,
      statuses: ['success', 'failed', 'success'] as const,
    };
    const { rerender } = render(
      <BankPickStep
        {...baseProps}
        progress={{ ...finished, statuses: [...finished.statuses] }}
        onGenerateMore={onGenerateMore}
      />
    );
    fireEvent.click(screen.getByRole('tab', { name: /^Generar$/ }));

    expect(screen.getByRole('region', { name: 'Progreso de creación de preguntas' })).toBeInTheDocument();
    expect(screen.getByText('2 de 3 preguntas listas. 1 no salieron del modelo.')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Generar una más' })).toBeNull();
    expect(screen.queryByRole('button', { name: /Generar en banco/ })).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: /Generar más/ }));
    expect(onGenerateMore).toHaveBeenCalledTimes(1);

    rerender(<BankPickStep {...baseProps} progress={null} onGenerateMore={onGenerateMore} />);
    expect(screen.getByRole('button', { name: 'Generar una más' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Generar en banco/ })).toBeInTheDocument();
    vi.restoreAllMocks();
  });
});
