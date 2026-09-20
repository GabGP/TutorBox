import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import * as httpClient from '../../../shared/api/httpClient';
import { TelemetryView } from '../TelemetryView';

const metrics = {
  total_generations: 10,
  successful_generations: 8,
  failed_generations: 2,
  success_rate: 0.8,
  avg_attempts: 1.5,
  avg_duration_ms: 3200,
};

function mockBackend(logs: unknown[]) {
  vi.spyOn(httpClient, 'requestApi').mockImplementation(
    async (_m: string, path: string) => {
      if (path.startsWith('/quiz/generation-metrics')) return metrics;
      if (path.startsWith('/quiz/generation-logs'))
        return { logs, total: logs.length };
      return {};
    }
  );
}

describe('TelemetryView', () => {
  it('renders metrics and logs', async () => {
    mockBackend([
      {
        id: 1,
        topic: 'sumas',
        model_name: 'qwen',
        attempts: 1,
        duration_ms: 3000,
        success: true,
      },
    ]);
    render(<TelemetryView />);
    await waitFor(() =>
      expect(screen.getByText(/10 intentos/)).toBeInTheDocument()
    );
    expect(screen.getByText(/sumas/)).toBeInTheDocument();
    vi.restoreAllMocks();
  });

  it('orders logs newest first even when the server returns oldest first', async () => {
    mockBackend([
      {
        id: 1,
        topic: 'arithmetic',
        subconcept: 'addition_subtraction',
        model_name: 'qwen',
        attempts: 1,
        duration_ms: 300,
        success: true,
        user_id: 7,
        question_id: 'q-old',
        rejection_history: [],
        created_at: '2026-09-01T10:00:00',
      },
      {
        id: 2,
        topic: 'fractions',
        subconcept: 'simplification',
        model_name: 'qwen',
        attempts: 2,
        duration_ms: 900,
        success: false,
        user_id: 7,
        question_id: null,
        rejection_history: ['Math mismatch'],
        created_at: '2026-09-02T10:00:00',
      },
    ]);
    render(<TelemetryView />);
    await waitFor(() =>
      expect(screen.getByText(/Fracciones/)).toBeInTheDocument()
    );
    // Newest (id 2, Fracciones) leads despite arriving last.
    const list = screen.getByRole('list', {
      name: 'Actividad de generación',
    });
    const items = within(list).getAllByRole('listitem');
    expect(items).toHaveLength(2);
    expect(items[0].textContent).toContain('Fracciones');
    expect(items[1].textContent).toContain('Aritmética');
    vi.restoreAllMocks();
  });

  it('opens the detail sheet on row tap with the full log info', async () => {
    mockBackend([
      {
        id: 9,
        topic: 'fractions',
        subconcept: 'simplification',
        model_name: 'qwen',
        attempts: 3,
        duration_ms: 1200,
        success: false,
        user_id: 7,
        question_id: 'q-abc',
        rejection_history: ['Math mismatch'],
        created_at: '2026-09-02T10:00:00',
      },
    ]);
    render(<TelemetryView />);
    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: 'Ver detalle generación 9' })
      ).toBeInTheDocument()
    );
    fireEvent.click(
      screen.getByRole('button', { name: 'Ver detalle generación 9' })
    );
    await waitFor(() =>
      expect(
        screen.getByRole('dialog', { name: 'Detalle de generación #9' })
      ).toBeInTheDocument()
    );
    const dialog =
      screen.getByRole('dialog', { name: 'Detalle de generación #9' })
        .textContent ?? '';
    expect(dialog).toContain('q-abc');
    expect(dialog).toContain('Math mismatch');
    expect(dialog).toContain('3');
    vi.restoreAllMocks();
  });

  it('renders latencies as min/sec', async () => {
    mockBackend([
      {
        id: 5,
        topic: 'arithmetic',
        model_name: 'qwen',
        attempts: 2,
        duration_ms: 75400,
        success: true,
        user_id: 7,
        question_id: null,
        rejection_history: [],
        created_at: '2026-09-03T10:00:00',
      },
    ]);
    render(<TelemetryView />);
    await waitFor(() =>
      expect(screen.getByText(/1 min 15s/)).toBeInTheDocument()
    );
    vi.restoreAllMocks();
  });

  it('formats latency units and percents', async () => {
    const { formatLatency, formatPercent } = await import(
      '../telemetryFormat'
    );
    expect(formatLatency(0)).toBe('0s');
    expect(formatLatency(29000)).toBe('29s');
    expect(formatLatency(60000)).toBe('1 min');
    expect(formatLatency(75400)).toBe('1 min 15s');
    expect(formatPercent(0.8958)).toBe('89.58%');
    expect(formatPercent(0.8)).toBe('80%');
  });

  it('renders the success rate as a real percent', async () => {
    mockBackend([]);
    render(<TelemetryView />);
    await waitFor(() =>
      expect(screen.getByText(/80% éxito/)).toBeInTheDocument()
    );
    vi.restoreAllMocks();
  });
});
