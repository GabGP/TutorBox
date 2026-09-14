import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ShinyText } from '../ShinyText/ShinyText';

describe('ShinyText Component', () => {
  it('renders text content with default span tag', () => {
    render(<ShinyText text="TutorBox está creando..." />);
    const el = screen.getByText('TutorBox está creando...');
    expect(el).toBeInTheDocument();
    expect(el.tagName.toLowerCase()).toBe('span');
  });

  it('renders with custom semantic tag when requested', () => {
    render(<ShinyText text="Generando con IA" as="h2" id="title" />);
    const heading = screen.getByRole('heading', { level: 2 });
    expect(heading).toBeInTheDocument();
    expect(heading).toHaveTextContent('Generando con IA');
    expect(heading).toHaveAttribute('id', 'title');
  });

  it('applies speed as a CSS custom property', () => {
    const { container } = render(<ShinyText text="Texto brillante" speed={3.2} />);
    const el = container.querySelector('span');
    expect(el?.style.getPropertyValue('--speed')).toBe('3.2s');
  });

  it('forwards custom class names', () => {
    const { container } = render(
      <ShinyText text="Clase adicional" className="custom-shiny-class" />
    );
    const el = container.querySelector('span');
    expect(el).toHaveClass('custom-shiny-class');
  });
});
