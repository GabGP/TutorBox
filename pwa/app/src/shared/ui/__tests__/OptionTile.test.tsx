import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { OptionTile } from '../OptionTile/OptionTile';

describe('OptionTile Component', () => {
  it('renders option letter and text label', () => {
    render(<OptionTile letter="B" text="25%" />);
    expect(screen.getByText('B')).toBeInTheDocument();
    expect(screen.getByText('25%')).toBeInTheDocument();
  });

  it('triggers onSelect with letter on click', () => {
    const onSelect = vi.fn();
    render(<OptionTile letter="C" text="42" onSelect={onSelect} />);

    fireEvent.click(screen.getByRole('button'));
    expect(onSelect).toHaveBeenCalledWith('C');
  });

  it('shows checkmark when isPicked is true', () => {
    render(<OptionTile letter="A" text="Solución" isPicked />);
    expect(screen.getByText('✓')).toBeInTheDocument();
    expect(screen.getByRole('button')).toHaveAttribute('aria-pressed', 'true');
  });

  it('disables interactions when locked or disabled', () => {
    const onSelect = vi.fn();
    render(
      <OptionTile letter="D" text="Opción D" isLocked onSelect={onSelect} />
    );

    fireEvent.click(screen.getByRole('button'));
    expect(onSelect).not.toHaveBeenCalled();
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
