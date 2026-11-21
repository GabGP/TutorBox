import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '../../../shared/api/httpClient';
import { systemHealthApi } from '../systemHealthApi';
import { useSystemHealth } from '../useSystemHealth';
import { EMPTY_SNAPSHOT, FULL_SNAPSHOT } from './systemHealthFixture';

const POLL_MS = 5000;

/** Lets the answer of the running sample land without moving the clock. */
async function settle() {
  await act(async () => {
    await Promise.resolve();
  });
}

async function advance(milliseconds: number) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(milliseconds);
  });
}

function setHidden(hidden: boolean) {
  Object.defineProperty(document, 'hidden', { configurable: true, get: () => hidden });
}

describe('useSystemHealth', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    setHidden(false);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    setHidden(false);
  });

  it('samples at once when opened, then every five seconds', async () => {
    const get = vi.spyOn(systemHealthApi, 'getSnapshot').mockResolvedValue(FULL_SNAPSHOT);
    const { result } = renderHook(() => useSystemHealth(true));
    await settle();
    expect(get).toHaveBeenCalledTimes(1);
    expect(result.current.snapshot).toEqual(FULL_SNAPSHOT);

    await advance(POLL_MS - 1);
    expect(get).toHaveBeenCalledTimes(1);
    await advance(1);
    expect(get).toHaveBeenCalledTimes(2);
  });

  it('never samples while closed', async () => {
    const get = vi.spyOn(systemHealthApi, 'getSnapshot').mockResolvedValue(FULL_SNAPSHOT);
    renderHook(() => useSystemHealth(false));
    await advance(POLL_MS * 3);

    expect(get).not.toHaveBeenCalled();
  });

  it('stops when closed and does not restart until opened again', async () => {
    const get = vi.spyOn(systemHealthApi, 'getSnapshot').mockResolvedValue(FULL_SNAPSHOT);
    const { rerender } = renderHook(({ open }) => useSystemHealth(open), { initialProps: { open: true } });
    await settle();

    rerender({ open: false });
    await advance(POLL_MS * 4);
    expect(get).toHaveBeenCalledTimes(1);

    rerender({ open: true });
    await settle();
    expect(get).toHaveBeenCalledTimes(2);
  });

  it('stops on unmount and ignores an answer that arrives late', async () => {
    let answer: (value: typeof FULL_SNAPSHOT) => void = () => undefined;
    const get = vi.spyOn(systemHealthApi, 'getSnapshot').mockReturnValue(
      new Promise((resolve) => {
        answer = resolve;
      })
    );
    const { result, unmount } = renderHook(() => useSystemHealth(true));
    unmount();

    await act(async () => answer(FULL_SNAPSHOT));
    await advance(POLL_MS * 2);

    expect(get).toHaveBeenCalledTimes(1);
    expect(result.current.snapshot).toBeNull();
  });

  it('skips the tick while the page is hidden and samples again once it is visible', async () => {
    const get = vi.spyOn(systemHealthApi, 'getSnapshot').mockResolvedValue(FULL_SNAPSHOT);
    renderHook(() => useSystemHealth(true));
    await settle();

    setHidden(true);
    await advance(POLL_MS);
    expect(get).toHaveBeenCalledTimes(1);

    setHidden(false);
    await advance(POLL_MS);
    expect(get).toHaveBeenCalledTimes(2);
  });

  it('keeps the last good sample and reports the error when a sample fails', async () => {
    const get = vi
      .spyOn(systemHealthApi, 'getSnapshot')
      .mockResolvedValueOnce(FULL_SNAPSHOT)
      .mockRejectedValueOnce(new ApiError('Sin conexión con Utz\'tutor', 0));
    const { result } = renderHook(() => useSystemHealth(true));
    await settle();

    await advance(POLL_MS);

    expect(get).toHaveBeenCalledTimes(2);
    expect(result.current.snapshot).toEqual(FULL_SNAPSHOT);
    expect(result.current.error).toBe("Sin conexión con Utz'tutor");
  });

  it('uses a generic message for a failure that is not an API error', async () => {
    vi.spyOn(systemHealthApi, 'getSnapshot').mockRejectedValue(new Error(''));
    const { result } = renderHook(() => useSystemHealth(true));
    await settle();

    expect(result.current.error).toBe('No se pudo leer el estado del Jetson. Se vuelve a intentar.');
  });

  it('refresh samples at once and restarts the five-second wait', async () => {
    const get = vi
      .spyOn(systemHealthApi, 'getSnapshot')
      .mockResolvedValueOnce(FULL_SNAPSHOT)
      .mockResolvedValueOnce(EMPTY_SNAPSHOT);
    const { result } = renderHook(() => useSystemHealth(true));
    await settle();

    await advance(2000);
    act(() => result.current.refresh());
    await settle();

    expect(get).toHaveBeenCalledTimes(2);
    expect(result.current.snapshot).toEqual(EMPTY_SNAPSHOT);
    await advance(POLL_MS - 1);
    expect(get).toHaveBeenCalledTimes(2);
  });
});
