import { act, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { SampleAge } from '../SampleAge';

describe('SampleAge', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-11-21T06:30:00Z'));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('counts the seconds since the sample, one line that ticks each second', async () => {
    render(<SampleAge sampledAt="2026-11-21T06:29:57Z" />);
    expect(screen.getByText('Actualizado hace 3 s')).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });

    expect(screen.getByText('Actualizado hace 5 s')).toBeInTheDocument();
  });

  it('never shows a negative age for a sample stamped a moment ahead', () => {
    render(<SampleAge sampledAt="2026-11-21T06:30:02Z" />);

    expect(screen.getByText('Actualizado hace 0 s')).toBeInTheDocument();
  });
});
