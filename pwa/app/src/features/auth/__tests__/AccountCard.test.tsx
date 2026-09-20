import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { AccountCard } from '../AccountCard';
import { authApi } from '../authApi';

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

  it('validates empty PIN change', () => {    render(
      <AccountCard
        user={user}
        onProfileChanged={vi.fn()}
        onSessionInvalidated={vi.fn()}
      />
    );
    fireEvent.click(screen.getByRole('button', { name: 'Cambiar PIN' }));
    expect(
      screen.getByText('Escribe tu PIN actual y el nuevo dos veces')
    ).toBeInTheDocument();
  });

  it('validates current PIN separately for username change', () => {
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
    fireEvent.click(screen.getByRole('button', { name: 'Cambiar nombre' }));
    expect(
      screen.getByText('Escribe tu PIN actual y el nombre nuevo')
    ).toBeInTheDocument();
  });

  it('rejects mismatched new PINs', () => {    render(
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
    fireEvent.click(screen.getByRole('button', { name: 'Cambiar PIN' }));
    expect(screen.getByText('Los dos PIN no coinciden')).toBeInTheDocument();
  });

  it('submits PIN change and refreshes profile', async () => {
    const spy = vi.spyOn(authApi, 'changePin').mockResolvedValue({} as never);
    const onProfileChanged = vi.fn();
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
    fireEvent.click(screen.getByRole('button', { name: 'Cambiar PIN' }));
    await waitFor(() =>
      expect(spy).toHaveBeenCalledWith('carlos', '1111', '2222')
    );
    expect(onProfileChanged).toHaveBeenCalled();
    spy.mockRestore();
  });

  it('submits username change and invalidates session', async () => {
    const spy = vi.spyOn(authApi, 'changeUsername').mockResolvedValue(undefined);
    const onSessionInvalidated = vi.fn();
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
    fireEvent.click(screen.getByRole('button', { name: 'Cambiar nombre' }));
    await waitFor(() =>
      expect(spy).toHaveBeenCalledWith('1111', 'carlos2')
    );
    expect(onSessionInvalidated).toHaveBeenCalled();
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
