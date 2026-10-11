import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '../../../shared/api/httpClient';
import { presenceApi } from '../presenceApi';
import { useClassPresence } from '../useClassPresence';
import { EMPTY_CLASS, MIXED_CLASS } from './presenceFixture';

const LOAD_ERROR = 'No se pudo cargar la lista de alumnos. Se vuelve a intentar.';

/** Lets the answer of the current poll land without moving the clock. */
async function flush() {
  await act(async () => {
    await Promise.resolve();
  });
}

async function advance(milliseconds: number) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(milliseconds);
  });
}

describe('useClassPresence', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('has no list until the first answer, then keeps the server order', async () => {
    let answer: (value: typeof MIXED_CLASS) => void = () => undefined;
    vi.spyOn(presenceApi, 'getClassPresence').mockReturnValue(
      new Promise((resolve) => {
        answer = resolve;
      })
    );
    const { result } = renderHook(() => useClassPresence(2000));
    expect(result.current).toEqual({ presence: null, error: null });

    await act(async () => answer(MIXED_CLASS));

    expect(result.current.presence).toEqual(MIXED_CLASS);
    expect(result.current.presence?.students.map((student) => student.username)).toEqual([
      'ana',
      'beto',
      'carla',
    ]);
  });

  it('polls every 2 seconds by default', async () => {
    const get = vi.spyOn(presenceApi, 'getClassPresence').mockResolvedValue(EMPTY_CLASS);
    renderHook(() => useClassPresence());
    await flush();
    expect(get).toHaveBeenCalledTimes(1);

    await advance(2000);
    expect(get).toHaveBeenCalledTimes(2);
  });

  it('polls on the given interval', async () => {
    const get = vi.spyOn(presenceApi, 'getClassPresence').mockResolvedValue(EMPTY_CLASS);
    renderHook(() => useClassPresence(2000));
    await flush();

    await advance(1999);
    expect(get).toHaveBeenCalledTimes(1);
    await advance(1);
    expect(get).toHaveBeenCalledTimes(2);
  });

  it('waits for a slow poll to finish before asking again', async () => {
    let finishSlowPoll: (value: typeof EMPTY_CLASS) => void = () => undefined;
    const get = vi
      .spyOn(presenceApi, 'getClassPresence')
      .mockReturnValueOnce(
        new Promise((resolve) => {
          finishSlowPoll = resolve;
        })
      )
      .mockResolvedValue(EMPTY_CLASS);
    renderHook(() => useClassPresence(2000));

    await advance(5000);
    expect(get).toHaveBeenCalledTimes(1);

    await act(async () => finishSlowPoll(EMPTY_CLASS));
    await advance(2000);
    expect(get).toHaveBeenCalledTimes(2);
  });

  it('keeps the last good list when a poll fails and reports the error', async () => {
    const serverError = new ApiError("Sin conexión con Utz'tutor", 0);
    const get = vi
      .spyOn(presenceApi, 'getClassPresence')
      .mockResolvedValueOnce(MIXED_CLASS)
      .mockRejectedValue(serverError);
    const { result } = renderHook(() => useClassPresence(2000));
    await flush();

    await advance(2000);

    expect(get).toHaveBeenCalledTimes(2);
    expect(result.current.presence).toEqual(MIXED_CLASS);
    expect(result.current.error).toBe("Sin conexión con Utz'tutor");
  });

  it('uses its own message for a failure that is not an API error', async () => {
    vi.spyOn(presenceApi, 'getClassPresence').mockRejectedValue(new TypeError('boom'));
    const { result } = renderHook(() => useClassPresence(2000));
    await flush();

    expect(result.current).toEqual({ presence: null, error: LOAD_ERROR });
  });

  it('clears the error on the next good poll', async () => {
    vi.spyOn(presenceApi, 'getClassPresence')
      .mockRejectedValueOnce(new Error('offline'))
      .mockResolvedValue(MIXED_CLASS);
    const { result } = renderHook(() => useClassPresence(2000));
    await flush();
    expect(result.current).toEqual({ presence: null, error: LOAD_ERROR });

    await advance(2000);

    expect(result.current).toEqual({ presence: MIXED_CLASS, error: null });
  });

  it('stops polling on unmount', async () => {
    const get = vi.spyOn(presenceApi, 'getClassPresence').mockResolvedValue(EMPTY_CLASS);
    const { unmount } = renderHook(() => useClassPresence(2000));
    await flush();

    unmount();
    await advance(10_000);

    expect(get).toHaveBeenCalledTimes(1);
  });
});
