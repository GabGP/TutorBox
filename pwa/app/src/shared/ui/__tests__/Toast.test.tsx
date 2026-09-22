import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ToastItemView } from '../Toast/ToastItem';
import { ToastViewport } from '../Toast/ToastViewport';
import { useToastQueue } from '../Toast/useToastQueue';

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

  it('pushes a success toast with status role', () => {
    render(<QueueHarness />);
    fireEvent.click(screen.getByRole('button', { name: 'push' }));
    expect(screen.getByRole('status')).toHaveTextContent('Cuenta eliminada.');
  });

  it('auto-dismisses on timeout', () => {
    render(<QueueHarness />);
    fireEvent.click(screen.getByRole('button', { name: 'push' }));
    expect(screen.getByRole('status')).toBeInTheDocument();
    act(() => {
      vi.advanceTimersByTime(4000);
    });
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('sticky toast (duration 0) never auto-dismisses', () => {
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

  it('dismisses on close button with close reason', () => {
    const onDismiss = vi.fn();
    render(
      <ToastViewport
        toasts={[{ id: 't1', message: 'Hola' }]}
        onDismiss={onDismiss}
      />
    );
    fireEvent.click(screen.getByRole('button', { name: 'Descartar aviso' }));
    expect(onDismiss).toHaveBeenCalledWith('t1', 'close');
  });

  it('dismisses on Escape with escape reason', () => {
    const onDismiss = vi.fn();
    render(
      <ToastItemView
        toast={{ id: 't1', message: 'Hola' }}
        onExit={onDismiss}
      />
    );
    fireEvent.keyDown(window, { key: 'Escape' });
    // window listener registered by the item
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    expect(onDismiss).toHaveBeenCalledWith('t1', 'escape');
  });

  it('dismisses on a long swipe with swipe reason', () => {
    const onExit = vi.fn();
    render(<ToastItemView toast={{ id: 't1', message: 'Hola' }} onExit={onExit} />);
    const toast = screen.getByRole('status');
    fireEvent.pointerDown(toast, { clientX: 200, clientY: 200, pointerId: 1 });
    fireEvent.pointerMove(toast, { clientX: 200, clientY: 260, pointerId: 1 });
    fireEvent.pointerUp(toast, { clientX: 200, clientY: 260, pointerId: 1 });
    expect(onExit).toHaveBeenCalledWith('t1', 'swipe');
  });

  it('snaps back on a short drag without dismissing', () => {
    const onExit = vi.fn();
    render(<ToastItemView toast={{ id: 't1', message: 'Hola' }} onExit={onExit} />);
    const toast = screen.getByRole('status');
    fireEvent.pointerDown(toast, { clientX: 200, clientY: 200, pointerId: 1 });
    fireEvent.pointerMove(toast, { clientX: 200, clientY: 210, pointerId: 1 });
    fireEvent.pointerUp(toast, { clientX: 200, clientY: 210, pointerId: 1 });
    expect(onExit).not.toHaveBeenCalled();
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
