import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { LoginForm } from '../LoginForm';

describe('LoginForm Component', () => {
  it('renders required input elements and enter button', () => {
    render(<LoginForm title="Iniciar sesión" onLogin={vi.fn()} />);

    expect(screen.getByPlaceholderText('Tu usuario')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('PIN')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Entrar' })).toBeInTheDocument();
  });

  it('validates empty username and PIN', async () => {
    const onLogin = vi.fn();
    render(<LoginForm title="Iniciar sesión" onLogin={onLogin} />);

    fireEvent.click(screen.getByRole('button', { name: 'Entrar' }));
    expect(screen.getByText('Escribe tu usuario y tu PIN')).toBeInTheDocument();
    expect(onLogin).not.toHaveBeenCalled();
  });

  it('allows toggling to signup mode when allowSignup is enabled', () => {
    render(
      <LoginForm
        title="Entra al juego"
        allowSignup
        onLogin={vi.fn()}
        onSignup={vi.fn()}
      />
    );

    const toggleBtn = screen.getByText('¿Primera vez? Crear cuenta');
    fireEvent.click(toggleBtn);

    expect(
      screen.getByRole('button', { name: 'Crear cuenta y entrar' })
    ).toBeInTheDocument();
  });
});
