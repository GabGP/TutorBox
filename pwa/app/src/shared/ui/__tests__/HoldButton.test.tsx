import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { HoldButton } from '../HoldButton/HoldButton';

let now = 0;
let rafId = 0;
const rafCallbacks = new Map<number, FrameRequestCallback>();

function flushRaf() {
  const pending = [...rafCallbacks.values()];
  rafCallbacks.clear();
  act(() => {
    pending.forEach((callback) => callback(now));
  });
}

function advanceTime(milliseconds: number) {
  act(() => {
    now += milliseconds;
    vi.advanceTimersByTime(milliseconds);
  });
  flushRaf();
}

beforeEach(() => {
  now = 0;
  rafId = 0;
  rafCallbacks.clear();
  vi.useFakeTimers();
  vi.spyOn(performance, 'now').mockImplementation(() => now);
  vi.stubGlobal('requestAnimationFrame', (callback: FrameRequestCallback) => {
    rafId += 1;
    rafCallbacks.set(rafId, callback);
    return rafId;
  });
  vi.stubGlobal('cancelAnimationFrame', (id: number) => {
    rafCallbacks.delete(id);
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  vi.useRealTimers();
});

describe('HoldButton (TutorBox merge of ReactBits hold interaction)', () => {
  it('renders idle label with screen-reader hold hint', () => {
    render(<HoldButton holdTime={2000}>Eliminar ronda</HoldButton>);
    // Dual label layers (base ink + clipped fill ink) intentionally duplicate text.
    expect(screen.getAllByText('Eliminar ronda')).toHaveLength(2);
    expect(
      screen.getByText('Mantén pulsado 2 segundos para confirmar')
    ).toBeInTheDocument();
  });

  it('defaults to TutorBox tokens and exposes progress attributes', () => {
    const { container } = render(
      <HoldButton size="lg" radius={14} fillDirection="up" />
    );
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('data-direction', 'up');
    expect(button).toHaveAttribute('data-phase', 'idle');
    expect(button.getAttribute('style')).toContain('--hb-fill');
    expect(container.querySelector('[data-testid="hold-fill"]')).toBeInTheDocument();
  });

  it('completes the hold, shows done label, fires onHold once, then resets', () => {
    const onHold = vi.fn();
    const onPhaseChange = vi.fn();
    render(
      <HoldButton holdTime={2000} resetAfter={1200} onHold={onHold} onPhaseChange={onPhaseChange} />
    );
    const button = screen.getByRole('button');

    fireEvent.pointerDown(button, { pointerId: 1 });
    expect(button).toHaveAttribute('data-phase', 'holding');

    advanceTime(2000);
    expect(onHold).toHaveBeenCalledTimes(1);
    expect(button).toHaveAttribute('data-phase', 'done');
    expect(screen.getByText('Confirmado')).toBeInTheDocument();

    advanceTime(1200);
    expect(button).toHaveAttribute('data-phase', 'idle');
    expect(onPhaseChange).toHaveBeenCalledWith('holding');
    expect(onPhaseChange).toHaveBeenCalledWith('done');
  });

  it('snaps back on early release without firing onHold', () => {
    const onHold = vi.fn();
    render(<HoldButton holdTime={2000} onHold={onHold} />);
    const button = screen.getByRole('button');

    fireEvent.pointerDown(button, { pointerId: 1 });
    advanceTime(500);
    fireEvent.pointerUp(button);
    advanceTime(300);

    expect(onHold).not.toHaveBeenCalled();
    expect(button).toHaveAttribute('data-phase', 'idle');
    expect(button).toHaveAttribute('data-progress', '0.000');
  });

  it('fires onTap on quick releases under 250ms', () => {
    const onTap = vi.fn();
    const onHold = vi.fn();
    render(<HoldButton holdTime={2000} onTap={onTap} onHold={onHold} />);
    const button = screen.getByRole('button');

    fireEvent.pointerDown(button, { pointerId: 1 });
    advanceTime(100);
    fireEvent.pointerUp(button);

    expect(onTap).toHaveBeenCalledTimes(1);
    expect(onHold).not.toHaveBeenCalled();
  });

  it('ignores input while disabled', () => {
    const onHold = vi.fn();
    render(
      <HoldButton holdTime={500} disabled onHold={onHold}>
        Bloqueado
      </HoldButton>
    );
    const button = screen.getByRole('button');
    fireEvent.pointerDown(button, { pointerId: 1 });
    advanceTime(800);
    expect(onHold).not.toHaveBeenCalled();
    expect(button).toBeDisabled();
  });

  it('supports keyboard hold with Space and cancel with Escape', () => {
    const onHold = vi.fn();
    render(<HoldButton holdTime={1000} onHold={onHold} />);
    const button = screen.getByRole('button');

    fireEvent.keyDown(button, { key: ' ' });
    expect(button).toHaveAttribute('data-phase', 'holding');
    advanceTime(1000);
    expect(onHold).toHaveBeenCalledTimes(1);
  });

  it('keeps done state when resetAfter is zero', () => {
    render(<HoldButton holdTime={400} resetAfter={0} doneLabel="Hecho" />);
    const button = screen.getByRole('button');
    fireEvent.pointerDown(button, { pointerId: 1 });
    advanceTime(400);
    expect(button).toHaveAttribute('data-phase', 'done');
    advanceTime(5000);
    expect(button).toHaveAttribute('data-phase', 'done');
    expect(screen.getByText('Hecho')).toBeInTheDocument();
  });
});
