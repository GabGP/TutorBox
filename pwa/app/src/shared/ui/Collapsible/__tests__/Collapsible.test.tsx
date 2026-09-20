import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { Collapsible } from '../Collapsible';

describe('Collapsible', () => {
  it('toggles expanded state and keeps content mounted', () => {
    render(
      <Collapsible title="Actividad de generación">
        <div>inner content</div>
      </Collapsible>
    );
    const toggle = screen.getByRole('button', {
      name: 'Actividad de generación',
    });
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    // Content stays mounted (like <details>) so inner state survives.
    expect(screen.getByText('inner content')).toBeInTheDocument();

    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    expect(
      screen.getByRole('region', { name: 'Actividad de generación' })
    ).toBeInTheDocument();

    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
  });

  it('supports custom id and defaultOpen', () => {
    render(
      <Collapsible title="Sección" id="sec" defaultOpen>
        <div>open content</div>
      </Collapsible>
    );
    expect(
      screen.getByRole('button', { name: 'Sección' })
    ).toHaveAttribute('aria-expanded', 'true');
    expect(document.getElementById('sec')).toBeInTheDocument();
    expect(screen.getByText('open content')).toBeInTheDocument();
  });
});
