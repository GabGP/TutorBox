import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { CountdownRing } from '../CountdownRing/CountdownRing';

describe('CountdownRing Component', () => {
  it('renders remaining seconds rounded up', () => {
    render(<CountdownRing remaining={12.4} duration={20} />);
    expect(screen.getByText('13')).toBeInTheDocument();
    expect(screen.getByRole('timer')).toHaveAttribute(
      'aria-label',
      '13 segundos restantes'
    );
  });

  it('renders nothing when remaining is null', () => {
    const { container } = render(<CountdownRing remaining={null} duration={20} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('adds low urgency class when remaining is 5 seconds or less', () => {
    const { container, rerender } = render(
      <CountdownRing remaining={5} duration={20} />
    );
    expect(container.firstChild).toHaveClass(/low/);

    rerender(<CountdownRing remaining={6} duration={20} />);
    expect(container.firstChild).not.toHaveClass(/low/);
  });
});
