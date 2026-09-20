import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { SwipeRow } from '../SwipeRow/SwipeRow';

const actions = [
  { key: 'info', label: 'Info', onActivate: vi.fn() },
  { key: 'del', label: 'Eliminar', tone: 'danger' as const, onActivate: vi.fn() },
];

describe('SwipeRow', () => {
  it('renders face content and actions', () => {
    render(<SwipeRow actions={actions}>Row text</SwipeRow>);
    expect(screen.getByText('Row text')).toBeInTheDocument();
    // Actions are plain buttons so keyboard users never need to swipe.
    expect(screen.getByRole('button', { name: 'Info' })).toBeInTheDocument();
  });

  it('opens via controlled prop and activates actions', () => {
    const onInfo = vi.fn();
    render(
      <SwipeRow
        open
        actions={[{ key: 'info', label: 'Info', onActivate: onInfo }]}
      >
        Row
      </SwipeRow>
    );
    const btn = screen.getByRole('button', { name: 'Info' });
    expect(btn).toBeInTheDocument();
    fireEvent.click(btn);
    expect(onInfo).toHaveBeenCalledTimes(1);
  });

  it('closes on Escape and notifies', () => {
    const onOpenChange = vi.fn();
    render(
      <SwipeRow open onOpenChange={onOpenChange} actions={actions}>
        Row
      </SwipeRow>
    );
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it('opens on a short drag past the threshold', () => {
    const onOpenChange = vi.fn();
    render(
      <SwipeRow onOpenChange={onOpenChange} actions={actions}>
        Row text
      </SwipeRow>
    );
    const face = screen.getByText('Row text');
    const root = face.parentElement!;
    Object.defineProperty(root.firstElementChild!, 'offsetWidth', {
      value: 192,
      configurable: true,
    });
    fireEvent.pointerDown(face, { clientX: 250 });
    fireEvent.pointerMove(face, { clientX: 200 }); // -50 past -40
    fireEvent.pointerUp(face, { clientX: 200 });
    expect(onOpenChange).toHaveBeenCalledWith(true);
    expect(root).toHaveAttribute('data-open', 'true');
  });

  it('clamps long drags at the strip width and opens', () => {
    render(<SwipeRow actions={actions}>Row text</SwipeRow>);
    const face = screen.getByText('Row text');
    const root = face.parentElement!;
    Object.defineProperty(root.firstElementChild!, 'offsetWidth', {
      value: 192,
      configurable: true,
    });
    fireEvent.pointerDown(face, { clientX: 250 });
    fireEvent.pointerMove(face, { clientX: 0 }); // clamped, no commit
    fireEvent.pointerUp(face, { clientX: 0 });
    expect(root).toHaveAttribute('data-open', 'true');
  });
});
