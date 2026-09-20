import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { SettingsView } from '../SettingsView';

describe('SettingsView accordion', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  function renderView() {
    render(
      <SettingsView
        user={{ id: 't1', username: 'profe', role: 'teacher' }}
        onProfileChanged={vi.fn()}
        onSessionInvalidated={vi.fn()}
        onClose={vi.fn()}
      />
    );
  }

  it('starts with all sections collapsed', () => {
    renderView();
    expect(screen.queryByText('Cambiar nombre')).not.toBeInTheDocument();
  });

  it('keeps content mounted through the close animation', () => {
    renderView();
    const header = screen.getByRole('button', { name: /Mi cuenta/ });
    fireEvent.click(header);
    expect(screen.getByText('Cambiar nombre')).toBeInTheDocument();

    fireEvent.click(header);
    // Still rendered while collapsing…
    expect(screen.getByText('Cambiar nombre')).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(400);
    });
    // …then unmounted.
    expect(screen.queryByText('Cambiar nombre')).not.toBeInTheDocument();
  });
});
