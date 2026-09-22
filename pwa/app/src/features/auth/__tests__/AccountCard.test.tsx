import { act, fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { AccountCard } from '../AccountCard';
import { authApi } from '../authApi';
import { advanceHold, setupHoldTimers, teardownHoldTimers } from '../../../test/holdTimers';

const user = { id: 'u1', username: 'carlos', role: 'student' as const };

describe('AccountCard', () => {
  it('renders profile row with username and role', () => {
    render(
      <AccountCard
        user={user}
        onProfileChanged={vi.fn()}
        onSessionInvalidated={vi.fn()}
      />
    );
    expect(screen.getByText('carlos')).toBeInTheDocument();
    expect(screen.getByText('Alumno')).toBeInTheDocument();
  });

  it('validates empty PIN change on hold', () => {
    setupHoldTimers();
    try {
      render(
        <AccountCard
          user={user}
          onProfileChanged={vi.fn()}
          onSessionInvalidated={vi.fn()}
        />
      );
      const holdBtn = screen.getByRole('button', { name: 'Cambiar PIN' });
      fireEvent.pointerDown(holdBtn, { pointerId: 1 });
      advanceHold(800);
      expect(
        screen.getByText('Escribe tu PIN actual y el nuevo dos veces')
      ).toBeInTheDocument();
    } finally {
      teardownHoldTimers();
    }
  });

  it('validates current PIN separately for username change on hold', () => {
    setupHoldTimers();
    try {
      render(
        <AccountCard
          user={user}
          onProfileChanged={vi.fn()}
          onSessionInvalidated={vi.fn()}
        />
      );
      fireEvent.change(screen.getByPlaceholderText('Nombre nuevo'), {
        target: { value: 'carlos2' },
      });
      const holdBtn = screen.getByRole('button', { name: 'Cambiar mi nombre' });
      fireEvent.pointerDown(holdBtn, { pointerId: 1 });
      advanceHold(2000);
      expect(
        screen.getByText('Escribe tu PIN actual y el nombre nuevo')
      ).toBeInTheDocument();
    } finally {
      teardownHoldTimers();
    }
  });

  it('rejects mismatched new PINs on hold', () => {
    setupHoldTimers();
    try {
      render(
        <AccountCard
          user={user}
          onProfileChanged={vi.fn()}
          onSessionInvalidated={vi.fn()}
        />
      );
      fireEvent.change(screen.getByPlaceholderText('PIN actual (para cambiar PIN)'), {
        target: { value: '1111' },
      });
      fireEvent.change(screen.getByPlaceholderText('PIN nuevo (4 a 8 números)'), {
        target: { value: '2222' },
      });
      fireEvent.change(screen.getByPlaceholderText('Repite el PIN nuevo'), {
        target: { value: '3333' },
      });
      const holdBtn = screen.getByRole('button', { name: 'Cambiar PIN' });
      fireEvent.pointerDown(holdBtn, { pointerId: 1 });
      advanceHold(800);
      expect(screen.getByText('Los dos PIN no coinciden')).toBeInTheDocument();
    } finally {
      teardownHoldTimers();
    }
  });

  it('submits PIN change on hold and refreshes profile', async () => {
    const spy = vi.spyOn(authApi, 'changePin').mockResolvedValue({} as never);
    const onProfileChanged = vi.fn();
    setupHoldTimers();
    try {
      render(
        <AccountCard
          user={user}
          onProfileChanged={onProfileChanged}
          onSessionInvalidated={vi.fn()}
        />
      );
      fireEvent.change(screen.getByPlaceholderText('PIN actual (para cambiar PIN)'), {
        target: { value: '1111' },
      });
      fireEvent.change(screen.getByPlaceholderText('PIN nuevo (4 a 8 números)'), {
        target: { value: '2222' },
      });
      fireEvent.change(screen.getByPlaceholderText('Repite el PIN nuevo'), {
        target: { value: '2222' },
      });
      const holdBtn = screen.getByRole('button', { name: 'Cambiar PIN' });
      fireEvent.click(holdBtn);
      expect(spy).not.toHaveBeenCalled();
      fireEvent.pointerDown(holdBtn, { pointerId: 1 });
      advanceHold(800);
      await act(async () => {});
      expect(spy).toHaveBeenCalledWith('carlos', '1111', '2222');
      expect(onProfileChanged).toHaveBeenCalled();
    } finally {
      teardownHoldTimers();
    }
    spy.mockRestore();
  });

  it('submits username change on hold and invalidates session', async () => {
    const spy = vi.spyOn(authApi, 'changeUsername').mockResolvedValue(undefined);
    const onSessionInvalidated = vi.fn();
    setupHoldTimers();
    try {
      render(
        <AccountCard
          user={user}
          onProfileChanged={vi.fn()}
          onSessionInvalidated={onSessionInvalidated}
        />
      );
      fireEvent.change(screen.getByPlaceholderText('PIN actual (para cambiar nombre)'), {
        target: { value: '1111' },
      });
      fireEvent.change(screen.getByPlaceholderText('Nombre nuevo'), {
        target: { value: 'carlos2' },
      });
      // Renaming edits your own account and ends the session: a plain
      // click never submits, only a full press-and-hold does.
      const holdBtn = screen.getByRole('button', { name: 'Cambiar mi nombre' });
      fireEvent.click(holdBtn);
      expect(spy).not.toHaveBeenCalled();
      fireEvent.pointerDown(holdBtn, { pointerId: 1 });
      advanceHold(2000);
      await act(async () => {});
      expect(spy).toHaveBeenCalledWith('1111', 'carlos2');
      expect(onSessionInvalidated).toHaveBeenCalled();
    } finally {
      teardownHoldTimers();
    }
    spy.mockRestore();
  });

  it('floats the rename confirmation as a toast and invalidates session', async () => {
    const spy = vi.spyOn(authApi, 'changeUsername').mockResolvedValue(undefined);
    const onSessionInvalidated = vi.fn();
    setupHoldTimers();
    try {
      render(
        <AccountCard
          user={user}
          onProfileChanged={vi.fn()}
          onSessionInvalidated={onSessionInvalidated}
        />
      );
      fireEvent.change(screen.getByPlaceholderText('PIN actual (para cambiar nombre)'), {
        target: { value: '1111' },
      });
      fireEvent.change(screen.getByPlaceholderText('Nombre nuevo'), {
        target: { value: 'carlos2' },
      });
      const holdBtn = screen.getByRole('button', { name: 'Cambiar mi nombre' });
      fireEvent.pointerDown(holdBtn, { pointerId: 1 });
      advanceHold(2000);
      await act(async () => {});
      expect(spy).toHaveBeenCalledWith('1111', 'carlos2');
      expect(onSessionInvalidated).toHaveBeenCalled();
      // Success floats as a toast; no inline notice banner shifts the card.
      expect(screen.getByRole('status')).toHaveTextContent(
        'Nombre actualizado. Inicia sesión de nuevo.'
      );
      expect(document.getElementById('accNote')).toBeNull();
    } finally {
      teardownHoldTimers();
    }
    spy.mockRestore();
  });

  it('ignores a plain click on rename without holding', () => {
    const spy = vi.spyOn(authApi, 'changeUsername').mockResolvedValue(undefined);
    render(
      <AccountCard
        user={user}
        onProfileChanged={vi.fn()}
        onSessionInvalidated={vi.fn()}
      />
    );
    fireEvent.change(screen.getByPlaceholderText('PIN actual (para cambiar nombre)'), {
      target: { value: '1111' },
    });
    fireEvent.change(screen.getByPlaceholderText('Nombre nuevo'), {
      target: { value: 'carlos2' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Cambiar mi nombre' }));
    expect(spy).not.toHaveBeenCalled();
    spy.mockRestore();
  });

  it('blocks forms while must_change_pin is pending', () => {
    render(
      <AccountCard
        user={{ ...user, must_change_pin: true }}
        onProfileChanged={vi.fn()}
        onSessionInvalidated={vi.fn()}
      />
    );
    expect(
      screen.getByText(/PIN temporal pendiente/)
    ).toBeInTheDocument();
    expect(screen.queryByPlaceholderText('PIN actual (para cambiar PIN)')).not.toBeInTheDocument();
  });
});
