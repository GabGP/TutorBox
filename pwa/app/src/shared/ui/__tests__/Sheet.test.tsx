import { fireEvent, render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { Sheet } from '../Sheet/Sheet';

describe('Sheet scroll lock', () => {
  it('locks body and root scroll while open, restores on close', () => {
    document.body.style.overflow = '';
    document.documentElement.style.overflow = '';
    const { unmount } = render(
      <Sheet label="Test sheet" onClose={() => {}}>
        content
      </Sheet>
    );
    expect(document.body.style.overflow).toBe('hidden');
    expect(document.documentElement.style.overflow).toBe('hidden');
    unmount();
    expect(document.body.style.overflow).toBe('');
    expect(document.documentElement.style.overflow).toBe('');
  });

  it('swallows backdrop touchmoves but lets sheet content scroll', () => {
    const { getByText, unmount } = render(
      <Sheet label="Test sheet" onClose={() => {}}>
        <span>inner</span>
      </Sheet>
    );
    const overlay = getByText('inner').closest(
      '[role="presentation"]'
    ) as HTMLElement;
    expect(overlay).toBeTruthy();

    const backdropTouch = new Event('touchmove', {
      bubbles: true,
      cancelable: true,
    });
    fireEvent(overlay, backdropTouch);
    expect(backdropTouch.defaultPrevented).toBe(true);

    const contentTouch = new Event('touchmove', {
      bubbles: true,
      cancelable: true,
    });
    fireEvent(getByText('inner'), contentTouch);
    expect(contentTouch.defaultPrevented).toBe(false);
    unmount();
  });
});
