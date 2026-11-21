import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { Spinner } from '../Spinner';

describe('Spinner', () => {
  it('is a status region named by its label, sized by its diameter', () => {
    render(<Spinner label="Cargando el modelo del tutor…" size={26} />);

    const spinner = screen.getByRole('status', { name: 'Cargando el modelo del tutor…' });
    expect(spinner).toHaveStyle({ width: '26px', height: '26px' });
  });

  it('defaults to 16 pixels', () => {
    render(<Spinner label="Cargando" />);

    expect(screen.getByRole('status', { name: 'Cargando' })).toHaveStyle({ width: '16px' });
  });
});
