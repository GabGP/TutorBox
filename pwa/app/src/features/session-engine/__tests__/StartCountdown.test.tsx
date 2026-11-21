import { act, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { StartCountdown } from '../StartCountdown';

describe('StartCountdown', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('counts 3, 2, 1 from the server value and then disappears', () => {
    render(<StartCountdown startsIn={3} />);

    expect(screen.getByRole('timer', { name: 'El juego empieza en 3' })).toBeInTheDocument();
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(screen.getByRole('timer', { name: 'El juego empieza en 2' })).toBeInTheDocument();
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(screen.getByRole('timer', { name: 'El juego empieza en 1' })).toBeInTheDocument();
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(screen.queryByRole('timer')).toBeNull();
  });

  it('follows a newer server value from the next poll', () => {
    const { rerender } = render(<StartCountdown startsIn={2.9} />);
    expect(screen.getByRole('timer', { name: 'El juego empieza en 3' })).toBeInTheDocument();

    rerender(<StartCountdown startsIn={1.2} />);

    expect(screen.getByRole('timer', { name: 'El juego empieza en 2' })).toBeInTheDocument();
  });

  it.each([null, undefined, 0])('shows nothing for starts_in %s', (startsIn) => {
    render(<StartCountdown startsIn={startsIn} />);

    expect(screen.queryByRole('timer')).toBeNull();
  });

  it('goes away when voting opens before the local countdown ends', () => {
    const { rerender } = render(<StartCountdown startsIn={3} />);

    rerender(<StartCountdown startsIn={0} />);

    expect(screen.queryByRole('timer')).toBeNull();
  });
});
