import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { TallyBars } from '../TallyBars/TallyBars';

describe('TallyBars Component', () => {
  const options = {
    A: '3/4',
    B: '1/2',
    C: '2/3',
    D: '1/4',
  };

  it('renders all four option rows with text labels', () => {
    render(<TallyBars options={options} />);
    expect(screen.getByText('3/4')).toBeInTheDocument();
    expect(screen.getByText('1/2')).toBeInTheDocument();
    expect(screen.getByText('2/3')).toBeInTheDocument();
    expect(screen.getByText('1/4')).toBeInTheDocument();
  });

  it('displays counts and percentage bars when revealed', () => {
    const counts = { A: 10, B: 5, C: 5, D: 0 };
    const { container } = render(
      <TallyBars options={options} counts={counts} totalVotes={20} />
    );

    expect(screen.getByText('10')).toBeInTheDocument();
    expect(screen.getAllByText('5')).toHaveLength(2);

    const fills = container.querySelectorAll('[style*="width"]');
    // A has 10/20 = 50%
    expect(fills[0]).toHaveStyle({ width: '50%' });
    // B has 5/20 = 25%
    expect(fills[1]).toHaveStyle({ width: '25%' });
  });
});
