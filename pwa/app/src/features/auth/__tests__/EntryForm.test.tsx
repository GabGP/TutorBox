import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { EntryForm, resolvePostLoginRedirect } from '../EntryForm';

describe('EntryForm Component', () => {
  it('renders required input elements and enter button', () => {
    render(<EntryForm title="Iniciar sesión" onLogin={vi.fn()} />);

    expect(screen.getByPlaceholderText('Tu usuario')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('PIN')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Entrar' })).toBeInTheDocument();
  });

  it('validates empty username and PIN', async () => {
    const onLogin = vi.fn();
    render(<EntryForm title="Iniciar sesión" onLogin={onLogin} />);

    fireEvent.click(screen.getByRole('button', { name: 'Entrar' }));
    // Validation floats as an error toast (assertive alert), not a banner.
    expect(screen.getByRole('alert')).toHaveTextContent(
      'Escribe tu usuario y tu PIN'
    );
    expect(onLogin).not.toHaveBeenCalled();
  });

  it('floats external errors as error toasts without shifting layout', () => {
    render(
      <EntryForm
        title="Panel del docente"
        onLogin={vi.fn()}
        externalError="Esta página es para docentes."
      />
    );
    expect(screen.getByRole('alert')).toHaveTextContent(
      'Esta página es para docentes.'
    );
    expect(screen.queryByTestId('toast-viewport')).toBeInTheDocument();
  });

  it('allows toggling to signup mode when allowSignup is enabled', () => {
    render(
      <EntryForm
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

  it('hides the signup toggle when allowSignup is false (staff portal)', () => {
    render(<EntryForm title="Panel del docente" onLogin={vi.fn()} />);

    expect(
      screen.queryByText('¿Primera vez? Crear cuenta')
    ).not.toBeInTheDocument();
  });
});

describe('resolvePostLoginRedirect', () => {
  it('keeps staff on /maestro/', () => {
    expect(resolvePostLoginRedirect('teacher', '/maestro/')).toBeNull();
    expect(resolvePostLoginRedirect('admin', '/maestro/')).toBeNull();
  });

  it('sends staff on /alumno/ to /maestro/', () => {
    expect(resolvePostLoginRedirect('teacher', '/alumno/')).toBe('/maestro/');
  });

  it('sends students on /maestro/ to /alumno/', () => {
    expect(resolvePostLoginRedirect('student', '/maestro/')).toBe('/alumno/');
  });

  it('keeps students on /alumno/', () => {
    expect(resolvePostLoginRedirect('student', '/alumno/')).toBeNull();
  });
});
