import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ToastItemView } from '../Toast/ToastItem';
import { ToastViewport } from '../Toast/ToastViewport';
import { useToastQueue } from '../Toast/useToastQueue';

/** Non-instant exits play the drop before removal. */
const EXIT_MS = 400 * 0.7 + 60;

function QueueHarness({ message = 'Cuenta eliminada.' }: { message?: string }) {
  const { toasts, pushToast, dismissToast } = useToastQueue();
  return (
    <div>
      <button type="button" onClick={() => pushToast({ message })}>
        push
      </button>
      <ToastViewport toasts={toasts} onDismiss={(id) => dismissToast(id)} />
    </div>
  );
}

describe('Toast queue + viewport', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('renders nothing when empty (no layout shift)', () => {
    render(<ToastViewport toasts={[]} onDismiss={vi.fn()} />);
    expect(screen.queryByTestId('toast-viewport')).not.toBeInTheDocument();
  });

  it('pushes a success toast with status role and tone icon', () => {
    render(<QueueHarness />);
    fireEvent.click(screen.getByRole('button', { name: 'push' }));
    expect(screen.getByRole('status')).toHaveTextContent('Cuenta eliminada.');
  });

  it('burns the fuse then plays the drop before removal', () => {
    render(<QueueHarness />);
    fireEvent.click(screen.getByRole('button', { name: 'push' }));
    act(() => {
      vi.advanceTimersByTime(4000);
    });
    // Drop-out still playing…
    expect(screen.getByRole('status')).toBeInTheDocument();
    act(() => {
      vi.advanceTimersByTime(EXIT_MS);
    });
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('sticky toast (duration 0) shows no fuse and never auto-dismisses', () => {
    render(
      <ToastViewport
        toasts={[{ id: 't1', message: 'PIN: 1234', duration: 0 }]}
        onDismiss={vi.fn()}
      />
    );
    act(() => {
      vi.advanceTimersByTime(20000);
    });
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('freezes the fuse on hover and resumes on leave', () => {
    const onDismiss = vi.fn();
    render(
      <ToastViewport
        toasts={[{ id: 't1', message: 'Hola' }]}
        onDismiss={onDismiss}
      />
    );
    act(() => {
      vi.advanceTimersByTime(3000);
    });
    fireEvent.pointerEnter(screen.getByRole('status'), { pointerType: 'mouse' });
    act(() => {
      vi.advanceTimersByTime(3000);
    });
    // Only ~1000ms burned: neither timed out nor closing.
    expect(onDismiss).not.toHaveBeenCalled();
    fireEvent.pointerLeave(screen.getByRole('status'), { pointerType: 'mouse' });
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    // Fuse burned out: drop-out playing…
    expect(onDismiss).not.toHaveBeenCalled();
    act(() => {
      vi.advanceTimersByTime(EXIT_MS);
    });
    expect(onDismiss).toHaveBeenCalledWith('t1', 'timeout');
  });

  it('dismisses on close button with close reason after the drop', () => {
    const onDismiss = vi.fn();
    render(
      <ToastViewport
        toasts={[{ id: 't1', message: 'Hola' }]}
        onDismiss={onDismiss}
      />
    );
    fireEvent.click(screen.getByRole('button', { name: 'Descartar aviso' }));
    expect(onDismiss).not.toHaveBeenCalled();
    act(() => {
      vi.advanceTimersByTime(EXIT_MS);
    });
    expect(onDismiss).toHaveBeenCalledWith('t1', 'close');
  });

  it('dismisses on Escape instantly with escape reason', () => {
    const onDismiss = vi.fn();
    render(
      <ToastItemView
        toast={{ id: 't1', message: 'Hola' }}
        onExit={onDismiss}
      />
    );
    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
      vi.advanceTimersByTime(0);
    });
    expect(onDismiss).toHaveBeenCalledWith('t1', 'escape');
  });

  it('dismisses on a long downward swipe with swipe reason', () => {
    const onExit = vi.fn();
    render(<ToastItemView toast={{ id: 't1', message: 'Hola' }} onExit={onExit} />);
    const toast = screen.getByRole('status');
    fireEvent.pointerDown(toast, { clientX: 200, clientY: 200, pointerId: 1 });
    fireEvent.pointerMove(toast, { clientX: 200, clientY: 215, pointerId: 1 });
    fireEvent.pointerMove(toast, { clientX: 200, clientY: 270, pointerId: 1 });
    fireEvent.pointerUp(toast, { clientX: 200, clientY: 270, pointerId: 1 });
    expect(onExit).not.toHaveBeenCalled();
    act(() => {
      vi.advanceTimersByTime(EXIT_MS);
    });
    expect(onExit).toHaveBeenCalledWith('t1', 'swipe');
  });

  it('ignores upward drags and snaps back without dismissing', () => {
    const onExit = vi.fn();
    render(<ToastItemView toast={{ id: 't1', message: 'Hola' }} onExit={onExit} />);
    const toast = screen.getByRole('status');
    fireEvent.pointerDown(toast, { clientX: 200, clientY: 260, pointerId: 1 });
    fireEvent.pointerMove(toast, { clientX: 200, clientY: 180, pointerId: 1 });
    fireEvent.pointerUp(toast, { clientX: 200, clientY: 180, pointerId: 1 });
    act(() => {
      vi.advanceTimersByTime(EXIT_MS + 500);
    });
    expect(onExit).not.toHaveBeenCalled();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('snaps back on a short drag without dismissing', () => {
    const onExit = vi.fn();
    render(<ToastItemView toast={{ id: 't1', message: 'Hola' }} onExit={onExit} />);
    const toast = screen.getByRole('status');
    fireEvent.pointerDown(toast, { clientX: 200, clientY: 200, pointerId: 1 });
    fireEvent.pointerMove(toast, { clientX: 200, clientY: 210, pointerId: 1 });
    fireEvent.pointerUp(toast, { clientX: 200, clientY: 210, pointerId: 1 });
    act(() => {
      vi.advanceTimersByTime(EXIT_MS + 500);
    });
    expect(onExit).not.toHaveBeenCalled();
  });

  it('runs the action before closing with action reason', () => {
    const onAction = vi.fn();
    const onDismiss = vi.fn();
    render(
      <ToastViewport
        toasts={[{ id: 't1', message: 'Eliminada', actionLabel: 'Deshacer', onAction }]}
        onDismiss={onDismiss}
      />
    );
    fireEvent.click(screen.getByRole('button', { name: 'Deshacer' }));
    expect(onAction).toHaveBeenCalledTimes(1);
    expect(onDismiss).not.toHaveBeenCalled();
    act(() => {
      vi.advanceTimersByTime(EXIT_MS);
    });
    expect(onDismiss).toHaveBeenCalledWith('t1', 'action');
  });

  it('renders description and custom icon, top fuse edge', () => {
    render(
      <ToastItemView
        toast={{
          id: 't1',
          message: 'Voz lista',
          description: 'Modelo cargado en memoria',
          icon: <span data-testid="custom-icon" />,
          fuse: 'top',
        }}
        onExit={vi.fn()}
      />
    );
    expect(screen.getByText('Modelo cargado en memoria')).toBeInTheDocument();
    expect(screen.getByTestId('custom-icon')).toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveAttribute('data-fuse', 'top');
  });

  it('hides the close button when closeButton is off', () => {
    render(
      <ToastItemView
        toast={{ id: 't1', message: 'Hola' }}
        closeButton={false}
        onExit={vi.fn()}
      />
    );
    expect(screen.queryByRole('button', { name: 'Descartar aviso' })).not.toBeInTheDocument();
  });

  it('error tone uses alert role', () => {
    render(
      <ToastViewport
        toasts={[{ id: 't1', message: 'Error grave', tone: 'error' }]}
        onDismiss={vi.fn()}
      />
    );
    expect(screen.getByRole('alert')).toHaveTextContent('Error grave');
  });

  it('caps the queue to protect memory', () => {
    function Flood() {
      const { toasts, pushToast, dismissToast } = useToastQueue(3);
      return (
        <div>
          <button
            type="button"
            onClick={() => {
              pushToast({ message: 'a' });
              pushToast({ message: 'b' });
              pushToast({ message: 'c' });
              pushToast({ message: 'd' });
            }}
          >
            flood
          </button>
          <ToastViewport toasts={toasts} onDismiss={(id) => dismissToast(id)} />
        </div>
      );
    }
    render(<Flood />);
    fireEvent.click(screen.getByRole('button', { name: 'flood' }));
    expect(screen.queryByText('a')).not.toBeInTheDocument();
    expect(screen.getByText('d')).toBeInTheDocument();
  });
});
