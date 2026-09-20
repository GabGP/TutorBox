import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import * as httpClient from '../../../shared/api/httpClient';
import { TelemetryView } from '../TelemetryView';

describe('TelemetryView', () => {
  it('renders metrics and logs', async () => {
    vi.spyOn(httpClient, 'requestApi').mockImplementation(
      async (_m: string, path: string) => {
        if (path.startsWith('/quiz/generation-metrics'))
          return {
            total_generations: 10,
            successful_generations: 8,
            failed_generations: 2,
            success_rate: 80,
            avg_attempts: 1.5,
            avg_duration_ms: 3200,
          };
        if (path.startsWith('/quiz/generation-logs'))
          return {
            logs: [
              {
                id: 1,
                topic: 'sumas',
                model_name: 'qwen',
                attempts: 1,
                duration_ms: 3000,
                success: true,
              },
            ],
            total: 1,
          };
        return {};
      }
    );
    render(<TelemetryView />);
    await waitFor(() =>
      expect(screen.getByText(/10 intentos/)).toBeInTheDocument()
    );
    expect(screen.getByText(/sumas/)).toBeInTheDocument();
    vi.restoreAllMocks();
  });
});
