import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { SettingsView, type SettingsSectionId } from '../SettingsView';

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
      />
    );
  }

  it('starts with all sections collapsed', () => {
    renderView();
    expect(screen.queryByText('Cambiar mi nombre')).not.toBeInTheDocument();
  });

  it('keeps content mounted through the close animation', () => {
    renderView();
    const header = screen.getByRole('button', { name: /Mi cuenta/ });
    fireEvent.click(header);
    // HoldButton renders dual ink layers (base + clipped fill).
    expect(screen.getAllByText('Cambiar mi nombre')).toHaveLength(2);

    fireEvent.click(header);
    // Still rendered while collapsing…
    expect(screen.getAllByText('Cambiar mi nombre')).toHaveLength(2);

    act(() => {
      vi.advanceTimersByTime(400);
    });
    // …then unmounted.
    expect(screen.queryByText('Cambiar mi nombre')).not.toBeInTheDocument();
  });
});

describe('SettingsView initialSection', () => {
  function renderWith(initialSection?: SettingsSectionId) {
    render(
      <SettingsView
        user={{ id: 't1', username: 'profe', role: 'teacher' }}
        onProfileChanged={vi.fn()}
        onSessionInvalidated={vi.fn()}
        roster={{ users: [], onAddStudent: vi.fn(), onResetPin: vi.fn() }}
        initialSection={initialSection}
      />
    );
  }

  it('opens the given row when the list mounts', () => {
    renderWith('usuarios');
    expect(screen.getByRole('button', { name: 'Usuarios' })).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText('Usuarios registrados')).toBeInTheDocument();
  });

  it('keeps every row closed when no section is given', () => {
    renderWith();
    expect(screen.getByRole('button', { name: 'Usuarios' })).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByText('Usuarios registrados')).not.toBeInTheDocument();
  });
});

describe('SettingsView Cerrar sesión', () => {
  it('ends the session from the last row of the list', () => {
    const onLogout = vi.fn();
    render(
      <SettingsView
        user={{ id: 't1', username: 'profe', role: 'teacher' }}
        onProfileChanged={vi.fn()}
        onSessionInvalidated={vi.fn()}
        onLogout={onLogout}
      />
    );
    fireEvent.click(screen.getByRole('button', { name: 'Cerrar sesión' }));
    expect(onLogout).toHaveBeenCalledTimes(1);
  });

  it('hides the row when no logout is given', () => {
    render(
      <SettingsView
        user={{ id: 't1', username: 'profe', role: 'teacher' }}
        onProfileChanged={vi.fn()}
        onSessionInvalidated={vi.fn()}
      />
    );
    expect(screen.queryByRole('button', { name: 'Cerrar sesión' })).not.toBeInTheDocument();
  });
});
