import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ProgressBar } from '../ProgressBar/ProgressBar';

describe('ProgressBar Component', () => {
  it('renders with accessibility progressbar role and calculated percentage', () => {
    render(<ProgressBar value={45} max={100} label="Progreso del quiz" />);
    const progressbar = screen.getByRole('progressbar', { name: 'Progreso del quiz' });
    expect(progressbar).toBeInTheDocument();
    expect(progressbar).toHaveAttribute('aria-valuenow', '45');
    expect(progressbar).toHaveAttribute('aria-valuemin', '0');
    expect(progressbar).toHaveAttribute('aria-valuemax', '100');
  });

  it('clamps values below 0 and above max correctly', () => {
    const { rerender } = render(<ProgressBar value={-20} max={100} />);
    let progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveAttribute('aria-valuenow', '0');

    rerender(<ProgressBar value={150} max={100} />);
    progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveAttribute('aria-valuenow', '100');
  });

  it('renders percentage label when showLabel is true', () => {
    render(<ProgressBar value={75} max={100} showLabel />);
    expect(screen.getByTestId('progress-label')).toHaveTextContent('75%');
  });

  it('renders animated shimmer beam by default and allows disabling it', () => {
    const { rerender } = render(<ProgressBar value={50} animated={true} />);
    expect(screen.getByTestId('progress-shimmer')).toBeInTheDocument();

    rerender(<ProgressBar value={50} animated={false} />);
    expect(screen.queryByTestId('progress-shimmer')).toBeNull();
  });

  it('renders whole-bar shimmer beam across track even when value is 0', () => {
    const { rerender } = render(<ProgressBar value={0} animated={true} />);
    expect(screen.getByTestId('progress-shimmer')).toBeInTheDocument();

    rerender(<ProgressBar value={0} animated={false} />);
    expect(screen.queryByTestId('progress-shimmer')).toBeNull();
  });

  it('applies custom size and class names', () => {
    const { container } = render(
      <ProgressBar value={25} size="lg" className="custom-progress" id="quiz-progress" />
    );
    const root = container.querySelector('#quiz-progress');
    expect(root).toHaveClass('custom-progress');
  });
});
