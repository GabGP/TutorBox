import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ClickerFaceBody } from '../ClickerFaceBody';
import type { ClickerDevice } from '../clickers.types';

const device: ClickerDevice = {
  device_id: 'ESP32-A4CF12',
  assigned_user_id: 1,
  assigned_username: 'ana',
  created_at: '2026-08-29 14:00:00',
  secret_issued_at: '2026-08-30 09:15:00',
};

function renderFace() {
  const onTap = vi.fn();
  render(<ClickerFaceBody device={device} onTap={onTap} />);
  return { onTap, idButton: screen.getByRole('button', { name: 'ESP32-A4CF12' }) };
}

describe('ClickerFaceBody id tap versus mouse drag', () => {
  it('a click after 60px of horizontal travel is the end of a drag and does not slide the row', () => {
    const { onTap, idButton } = renderFace();
    fireEvent.pointerDown(idButton, { clientX: 100, pointerId: 1 });
    fireEvent.click(idButton, { clientX: 160 });
    expect(onTap).not.toHaveBeenCalled();
  });

  it('a click after 3px of travel is still a tap and slides the row', () => {
    const { onTap, idButton } = renderFace();
    fireEvent.pointerDown(idButton, { clientX: 100, pointerId: 1 });
    fireEvent.click(idButton, { clientX: 103 });
    expect(onTap).toHaveBeenCalledTimes(1);
  });

  it('a click with no preceding press (keyboard activation) slides the row', () => {
    const { onTap, idButton } = renderFace();
    fireEvent.click(idButton);
    expect(onTap).toHaveBeenCalledTimes(1);
  });

  it('a drag-click does not leak into the next click', () => {
    const { onTap, idButton } = renderFace();
    fireEvent.pointerDown(idButton, { clientX: 100, pointerId: 1 });
    fireEvent.click(idButton, { clientX: 160 });
    expect(onTap).not.toHaveBeenCalled();
    fireEvent.click(idButton);
    expect(onTap).toHaveBeenCalledTimes(1);
  });

  it('a press that never clicked does not swallow a later keyboard activation', () => {
    const { onTap, idButton } = renderFace();
    fireEvent.pointerDown(idButton, { clientX: 100, pointerId: 1 });
    fireEvent.keyDown(idButton, { key: 'Enter' });
    fireEvent.click(idButton);
    expect(onTap).toHaveBeenCalledTimes(1);
  });
});
