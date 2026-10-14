import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '../../../shared/api/httpClient';
import { rosterApi } from '../../roster/rosterApi';
import { clickersApi } from '../clickersApi';
import type { ClickerDevice } from '../clickers.types';
import { CLICKER_REFRESH_INTERVAL_MS, useClickerFleet } from '../useClickerFleet';
import { FLEET_SEED } from './clickerFixture';

const NEW_CLICKER: ClickerDevice = {
  device_id: 'ESP32-N1',
  assigned_user_id: null,
  assigned_username: null,
  created_at: '2026-10-13 11:58:00',
  secret_issued_at: '2026-10-13 11:58:00',
};

/** A promise whose answer the test delivers when it chooses. */
interface Deferred<T> {
  promise: Promise<T>;
  resolve: (value: T) => void;
}

function deferred<T>(): Deferred<T> {
  let resolve: (value: T) => void = () => undefined;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}

/** Moves the fake clock forward and lets the answers that land meanwhile run. */
async function advance(milliseconds: number) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(milliseconds);
  });
}

/** Lets answers that are already waiting land, without moving the clock. */
async function settle() {
  await advance(0);
}

/** Switches the page between visible and hidden, as a phone does when locked or backgrounded. */
function showPage(state: 'visible' | 'hidden') {
  Object.defineProperty(document, 'visibilityState', { configurable: true, value: state });
  act(() => {
    document.dispatchEvent(new Event('visibilitychange'));
  });
}

function deviceIds(devices: ClickerDevice[]): string[] {
  return devices.map((device) => device.device_id);
}

/** Answers every device-list request with a fresh copy of the seed fleet. */
function spyOnListDevices() {
  return vi
    .spyOn(clickersApi, 'listDevices')
    .mockImplementation(async () => FLEET_SEED.map((device) => ({ ...device })));
}

describe('useClickerFleet periodic reload', () => {
  let listDevices: ReturnType<typeof spyOnListDevices>;

  beforeEach(() => {
    vi.useFakeTimers();
    listDevices = spyOnListDevices();
    vi.spyOn(rosterApi, 'getStudents').mockResolvedValue([]);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    Reflect.deleteProperty(document, 'visibilityState');
  });

  it('is 5 seconds', () => {
    expect(CLICKER_REFRESH_INTERVAL_MS).toBe(5000);
  });

  it('loads once, then reloads every 5 seconds while mounted', async () => {
    renderHook(() => useClickerFleet());
    await settle();
    expect(listDevices).toHaveBeenCalledTimes(1);

    await advance(CLICKER_REFRESH_INTERVAL_MS - 1);
    expect(listDevices).toHaveBeenCalledTimes(1);
    await advance(1);
    expect(listDevices).toHaveBeenCalledTimes(2);
    await advance(CLICKER_REFRESH_INTERVAL_MS);
    expect(listDevices).toHaveBeenCalledTimes(3);
  });

  it('shows a clicker that a periodic reload brings, without raising the loading flag', async () => {
    const { result } = renderHook(() => useClickerFleet());
    await settle();
    expect(result.current.loading).toBe(false);

    const periodicAnswer = deferred<ClickerDevice[]>();
    listDevices.mockReturnValueOnce(periodicAnswer.promise);
    await advance(CLICKER_REFRESH_INTERVAL_MS);
    expect(result.current.loading).toBe(false);

    await act(async () => periodicAnswer.resolve([...FLEET_SEED, NEW_CLICKER]));
    expect(deviceIds(result.current.devices)).toContain('ESP32-N1');
    expect(result.current.loading).toBe(false);
  });

  it('does not reload while the page is hidden', async () => {
    renderHook(() => useClickerFleet());
    await settle();

    showPage('hidden');
    await advance(CLICKER_REFRESH_INTERVAL_MS * 3);
    expect(listDevices).toHaveBeenCalledTimes(1);
  });

  it('reloads at once when the page becomes visible again', async () => {
    renderHook(() => useClickerFleet());
    await settle();
    showPage('hidden');
    await advance(CLICKER_REFRESH_INTERVAL_MS);
    expect(listDevices).toHaveBeenCalledTimes(1);

    showPage('visible');
    expect(listDevices).toHaveBeenCalledTimes(2);
    await settle();
  });

  it('keeps the list and shows no toast when a periodic reload fails, then tries again', async () => {
    const { result } = renderHook(() => useClickerFleet());
    await settle();
    expect(result.current.devices).toHaveLength(FLEET_SEED.length);

    listDevices.mockRejectedValueOnce(new ApiError('', 500));
    await advance(CLICKER_REFRESH_INTERVAL_MS);
    expect(result.current.devices).toHaveLength(FLEET_SEED.length);
    expect(result.current.toasts).toEqual([]);

    listDevices.mockResolvedValueOnce([...FLEET_SEED, NEW_CLICKER]);
    await advance(CLICKER_REFRESH_INTERVAL_MS);
    expect(deviceIds(result.current.devices)).toContain('ESP32-N1');
    expect(result.current.toasts).toEqual([]);
  });

  it('still toasts a failed reload that follows a mutation', async () => {
    const { result } = renderHook(() => useClickerFleet());
    await settle();
    vi.spyOn(clickersApi, 'registerDevice').mockResolvedValue(NEW_CLICKER);
    listDevices.mockRejectedValueOnce(new ApiError('', 500));

    await act(async () => {
      await result.current.registerClicker('ESP32-N1');
    });
    expect(result.current.toasts.map((toast) => toast.message)).toEqual([
      'Error al cargar clickers',
    ]);
  });

  it('does not let an older periodic answer overwrite a list a mutation just reloaded', async () => {
    const { result } = renderHook(() => useClickerFleet());
    await settle();

    const periodicAnswer = deferred<ClickerDevice[]>();
    listDevices.mockReturnValueOnce(periodicAnswer.promise);
    await advance(CLICKER_REFRESH_INTERVAL_MS);

    vi.spyOn(clickersApi, 'registerDevice').mockResolvedValue(NEW_CLICKER);
    listDevices.mockResolvedValueOnce([...FLEET_SEED, NEW_CLICKER]);
    await act(async () => {
      await result.current.registerClicker('ESP32-N1');
    });
    expect(deviceIds(result.current.devices)).toContain('ESP32-N1');

    await act(async () => periodicAnswer.resolve([...FLEET_SEED]));
    expect(deviceIds(result.current.devices)).toContain('ESP32-N1');
  });

  it('a late answer after unmount starts no reload and throws nothing', async () => {
    const { unmount } = renderHook(() => useClickerFleet());
    await settle();

    const periodicAnswer = deferred<ClickerDevice[]>();
    listDevices.mockReturnValueOnce(periodicAnswer.promise);
    await advance(CLICKER_REFRESH_INTERVAL_MS);
    unmount();

    await act(async () => periodicAnswer.resolve([...FLEET_SEED, NEW_CLICKER]));
    await advance(CLICKER_REFRESH_INTERVAL_MS * 2);
    expect(listDevices).toHaveBeenCalledTimes(2);
  });

  it('stops its timer and its visibility listener on unmount', async () => {
    const { unmount } = renderHook(() => useClickerFleet());
    await settle();
    unmount();

    await advance(CLICKER_REFRESH_INTERVAL_MS * 3);
    showPage('visible');
    expect(listDevices).toHaveBeenCalledTimes(1);
  });
});
