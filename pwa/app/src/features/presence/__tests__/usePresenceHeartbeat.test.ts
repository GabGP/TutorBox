import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { presenceApi } from '../presenceApi';
import { HEARTBEAT_INTERVAL_MS, usePresenceHeartbeat } from '../usePresenceHeartbeat';

/** Switches the page between visible and hidden, as a phone does when locked or backgrounded. */
function showPage(state: 'visible' | 'hidden') {
  Object.defineProperty(document, 'visibilityState', { configurable: true, value: state });
  document.dispatchEvent(new Event('visibilitychange'));
}

async function advance(milliseconds: number) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(milliseconds);
  });
}

/** Replaces the network call with a resolved spy; each test can queue failures on it. */
function spyOnHeartbeat() {
  return vi.spyOn(presenceApi, 'sendHeartbeat').mockResolvedValue(undefined);
}

describe('usePresenceHeartbeat', () => {
  let sendHeartbeat: ReturnType<typeof spyOnHeartbeat>;

  beforeEach(() => {
    vi.useFakeTimers();
    sendHeartbeat = spyOnHeartbeat();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    Reflect.deleteProperty(document, 'visibilityState');
  });

  it('beats once straight away when enabled', () => {
    renderHook(() => usePresenceHeartbeat({ enabled: true }));
    expect(sendHeartbeat).toHaveBeenCalledTimes(1);
  });

  it('keeps beating every 5 seconds', async () => {
    renderHook(() => usePresenceHeartbeat({ enabled: true }));

    await advance(HEARTBEAT_INTERVAL_MS - 1);
    expect(sendHeartbeat).toHaveBeenCalledTimes(1);

    await advance(1);
    expect(sendHeartbeat).toHaveBeenCalledTimes(2);

    await advance(HEARTBEAT_INTERVAL_MS);
    expect(sendHeartbeat).toHaveBeenCalledTimes(3);
  });

  it('is 5 seconds by default', () => {
    expect(HEARTBEAT_INTERVAL_MS).toBe(5000);
  });

  it('honours a custom interval', async () => {
    renderHook(() => usePresenceHeartbeat({ enabled: true, intervalMs: 1000 }));
    await advance(3000);
    expect(sendHeartbeat).toHaveBeenCalledTimes(4);
  });

  it('sends nothing while disabled', async () => {
    renderHook(() => usePresenceHeartbeat({ enabled: false }));
    await advance(20_000);
    expect(sendHeartbeat).not.toHaveBeenCalled();
  });

  it('starts beating once it becomes enabled', async () => {
    const { rerender } = renderHook(
      ({ enabled }: { enabled: boolean }) => usePresenceHeartbeat({ enabled }),
      { initialProps: { enabled: false } }
    );
    expect(sendHeartbeat).not.toHaveBeenCalled();

    rerender({ enabled: true });
    expect(sendHeartbeat).toHaveBeenCalledTimes(1);
  });

  it('stops beating when it becomes disabled', async () => {
    const { rerender } = renderHook(
      ({ enabled }: { enabled: boolean }) => usePresenceHeartbeat({ enabled }),
      { initialProps: { enabled: true } }
    );
    rerender({ enabled: false });

    await advance(HEARTBEAT_INTERVAL_MS * 3);
    expect(sendHeartbeat).toHaveBeenCalledTimes(1);
  });

  it('beats again at once when the page becomes visible', () => {
    renderHook(() => usePresenceHeartbeat({ enabled: true }));
    expect(sendHeartbeat).toHaveBeenCalledTimes(1);

    act(() => showPage('visible'));
    expect(sendHeartbeat).toHaveBeenCalledTimes(2);
  });

  it('does not beat when the page is hidden', () => {
    renderHook(() => usePresenceHeartbeat({ enabled: true }));

    act(() => showPage('hidden'));
    expect(sendHeartbeat).toHaveBeenCalledTimes(1);
  });

  it('ignores a failed beat and keeps beating', async () => {
    sendHeartbeat.mockRejectedValueOnce(new Error('offline'));
    renderHook(() => usePresenceHeartbeat({ enabled: true }));

    await advance(HEARTBEAT_INTERVAL_MS);
    expect(sendHeartbeat).toHaveBeenCalledTimes(2);
  });

  it('stops its timer and its visibility listener on unmount', async () => {
    const { unmount } = renderHook(() => usePresenceHeartbeat({ enabled: true }));
    unmount();

    await advance(HEARTBEAT_INTERVAL_MS * 3);
    act(() => showPage('visible'));
    expect(sendHeartbeat).toHaveBeenCalledTimes(1);
  });
});
