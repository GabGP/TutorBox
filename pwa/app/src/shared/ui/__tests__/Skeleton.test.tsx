import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { Skeleton } from '../Skeleton/Skeleton';

describe('Skeleton', () => {
  it('renders a hidden placeholder block with sizing', () => {
    const { container } = render(
      <Skeleton style={{ width: '60%', height: '16px' }} />
    );
    const el = container.firstElementChild!;
    expect(el.tagName).toBe('SPAN');
    expect(el).toHaveAttribute('aria-hidden', 'true');
    expect(el).toHaveStyle({ width: '60%', height: '16px' });
  });
});
