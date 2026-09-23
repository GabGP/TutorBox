import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

let mockMode: string | null = 'apps';
vi.mock('../../../features/mode/useApplianceMode', () => ({
  useApplianceMode: () => ({ mode: mockMode, error: null, saving: false, setMode: vi.fn() }),
}));
vi.mock('../../../features/session-engine/useSessionEngine', () => ({
  useSessionEngine: () => ({ session: null, error: null, refresh: vi.fn(), setSession: vi.fn() }),
}));

import { DisplayView } from '../DisplayView';

describe('DisplayView follows the classroom mode', () => {
  it('shows the download address in take-home mode', () => {
    mockMode = 'apps';
    render(<DisplayView />);
    expect(screen.getByText(/descargas/)).toBeInTheDocument();
  });

  it('keeps the quiz idle screen in quiz mode', () => {
    mockMode = 'quiz';
    render(<DisplayView />);
    expect(screen.getByText('TutorBox está listo')).toBeInTheDocument();
  });
});
